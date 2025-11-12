from openai import OpenAI
import telebot
import os
from dotenv import load_dotenv

# Загружаем ключи из .env
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Инициализация бота и клиента OpenAI
bot = telebot.TeleBot(TELEGRAM_TOKEN)
client = OpenAI(api_key=OPENAI_API_KEY)

# Функция для запроса к ChatGPT
def ask_gpt(prompt):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Ты — дружелюбный и профессиональный ассистент туристического агентства "
                        "«КОКОС ТУР», которое помогает людям подобрать отдых, авиабилеты, "
                        "туры, отели и визовую поддержку. "
                        "Отвечай от имени компании «КОКОС ТУР» — пиши вежливо, позитивно и уверенно. "
                        "Если пользователь задаёт вопрос о путешествиях, направлениях или туризме, "
                        "давай подробные ответы и советы. Если вопрос не по теме туризма — всё равно "
                        "отвечай дружелюбно от имени «КОКОС ТУР» и вежливо проси для точной информацией и по вопросам бронирования отправлять менеджерам это Малик и Владислав номер телефона Малика +998900120600 номер телефона Владислава +998971779848"
                    )
                },
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Ошибка: {e}"

# Обработка сообщений пользователей
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_input = message.text
    print(f"Пользователь: {user_input}")  # лог в консоль
    reply = ask_gpt(user_input)
    print(f"БОТ: {reply}\n")  # лог в консоль
    bot.reply_to(message, reply)

print("✅ Бот «КОКОС ТУР» запущен и готов к работе!")
bot.polling()