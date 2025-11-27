import telebot
import requests
import jsons
from Class_ModelResponse import ModelResponse

# Замените 'YOUR_BOT_TOKEN' на ваш токен от BotFather
# модель -
API_TOKEN = '8027126676:AAEuID1MwgBJhHqx25rOZHRa4fqhTmP0CVk'
bot = telebot.TeleBot(API_TOKEN)

# Хранилище контекста для каждого пользователя
user_contexts = {}

# Команды
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "Привет! Я ваш Telegram бот.\n"
        "Доступные команды:\n"
        "/start - вывод всех доступных команд\n"
        "/model - выводит название используемой языковой модели\n"
        "/clear - очистить историю диалога\n"  
        "Отправьте любое сообщение, и я отвечу с помощью LLM модели."
    )
    bot.reply_to(message, welcome_text)


@bot.message_handler(commands=['model'])
def send_model_name(message):
    # Отправляем запрос к LM Studio для получения информации о модели
    response = requests.get('http://localhost:1234/v1/models')

    if response.status_code == 200:
        model_info = response.json()
        model_name = model_info['data'][0]['id']
        bot.reply_to(message, f"Используемая модель: {model_name}")
    else:
        bot.reply_to(message, 'Не удалось получить информацию о модели.')


@bot.message_handler(commands=['clear'])
def clear_context(message):
    user_id = message.from_user.id

    user_contexts[user_id] = []
    bot.reply_to(message, "История диалога очищена")


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    user_query = message.text

    # Получаем или создаем контекст для пользователя
    if user_id not in user_contexts:
        user_contexts[user_id] = []  # Контекст - это список сообщений

    # Добавляем новый запрос пользователя в контекст
    user_message = {"role": "user", "content": user_query}
    user_contexts[user_id].append(user_message)

    # Формируем запрос к API, включающий ВЕСЬ контекст
    request = {
        "messages": user_contexts[user_id]  # Отправляем всю историю диалога
    }

    # Отправляем запрос к модели
    response = requests.post(
        'http://localhost:1234/v1/chat/completions',
        json=request
    )

    # Обрабатываем ответ
    if response.status_code == 200:
        model_response: ModelResponse = jsons.loads(response.text, ModelResponse)
        assistant_reply = model_response.choices[0].message.content

        # Добавляем ответ ассистента в контекст пользователя
        assistant_message = {"role": "assistant", "content": assistant_reply}
        user_contexts[user_id].append(assistant_message)

        # Отправляем ответ пользователю
        bot.reply_to(message, assistant_reply)
    else:
        # Если ошибка, не добавляем сообщение ассистента в контекст
        error_text = f'Произошла ошибка при обращении к модели. Статус код: {response.status_code}'
        bot.reply_to(message, error_text)
        # Можно также залогировать response.text для деталей ошибки


# Запуск бота
if __name__ == '__main__':
    bot.polling(none_stop=True)