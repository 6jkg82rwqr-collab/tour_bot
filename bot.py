from openai import OpenAI
import telebot
import os
from dotenv import load_dotenv
from datetime import datetime

# Загружаем ключи из .env
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
client = OpenAI(api_key=OPENAI_API_KEY)

# 🔹 Твой Telegram ID (узнай у @userinfobot)
ADMIN_ID = 7928610544  # 👈 замени на свой ID

# 🔹 Память пользователей
user_sessions = {}

# 🔹 Вопросы для анкеты
questions = [
    "Как вас зовут? 😊",
    "Пожалуйста, укажите номер телефона, чтобы менеджер мог связаться с вами 📱",
    "Куда вы хотите отправиться? 🌴",
    "На сколько человек планируете поездку?",
    "На сколько дней хотите отдохнуть?",
    "Какие даты вылета вас интересуют? 📅"
]

# --- 🧠 ChatGPT ответы ---
def ask_gpt(prompt):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Ты — дружелюбный и профессиональный ассистент туристического агентства "
                        "«КОКОС ТУР». Помогаешь клиентам подобрать отдых, туры, отели и визы. "
                        "Отвечай от имени компании «КОКОС ТУР» — пиши вежливо, позитивно и уверенно. "
                        "Если вопрос не по теме туризма — оставайся дружелюбным и напомни, что "
                        "по вопросам бронирования можно обращаться к менеджерам: Малик (+998900120600) "
                        "и Владислав (+998971779848)."
                    )
                },
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Ошибка: {e}"

# --- 🟢 /start ---
@bot.message_handler(commands=["start"])
def start(message):
    chat_id = message.chat.id
    user = message.from_user
    username = user.username or "—"

    # Создаём новую сессию
    user_sessions[chat_id] = {
        "step": 0,
        "data": {},
        "history": [],
        "greeted": True,
        "username": username,
        "first_seen": datetime.now().strftime("%d.%m.%Y %H:%M")
    }

    bot.send_message(
        chat_id,
        "Привет! 👋 Я виртуальный помощник турагентства «КОКОС ТУР» 🌴\n"
        "Помогу подобрать идеальный отдых 😎\n\n" + questions[0]
    )

    # 📬 Уведомляем админа о новом пользователе
    bot.send_message(
        ADMIN_ID,
        f"📨 Новый пользователь обратился к боту:\n\n"
        f"🧍‍♂️ Имя: {user.first_name or '—'}\n"
        f"👤 Username: @{username}\n"
        f"🆔 ID: {chat_id}\n"
        f"⏰ Время: {user_sessions[chat_id]['first_seen']}\n\n"
        f"💬 Стартовал диалог с ботом «КОКОС ТУР» 🌴"
    )

# --- 💬 Обработка сообщений ---
@bot.message_handler(func=lambda msg: True)
def handle_message(message):
    chat_id = message.chat.id
    text = message.text.strip()

    # Если сессии нет — обычный диалог через ChatGPT
    if chat_id not in user_sessions:
        user_sessions[chat_id] = {"greeted": True, "history": []}

    session = user_sessions[chat_id]
    session["history"].append(f"👤 {text}")

    # Проверяем, идёт ли анкета
    if "step" in session:
        step = session["step"]
        data = session.get("data", {})
        data[f"q{step}"] = text
        step += 1

        if step < len(questions):
            session["step"] = step
            bot.send_message(chat_id, questions[step])
        else:
            # Анкета завершена
            name = data.get("q0", "—")
            phone = data.get("q1", "—")
            destination = data.get("q2", "—")
            people = data.get("q3", "—")
            days = data.get("q4", "—")
            dates = data.get("q5", "—")

            # Добавляем ответы в историю
            session["history"].append("✅ Анкета завершена")

            summary = (
                f"📋 <b>Новая заявка от клиента:</b>\n\n"
                f"👤 Имя: {name}\n"
                f"📱 Телефон: {phone}\n"
                f"🌍 Направление: {destination}\n"
                f"👨‍👩‍👧 Кол-во человек: {people}\n"
                f"🕒 Кол-во дней: {days}\n"
                f"📅 Даты вылета: {dates}\n\n"
                f"Отправлено из бота «КОКОС ТУР» 🌴"
            )

            # 📨 Отправляем админу заявку и историю общения
            history_text = "\n".join(session["history"][-10:])  # последние 10 сообщений
            admin_report = (
                f"📬 <b>История общения с пользователем:</b>\n"
                f"🧍‍♂️ ID: {chat_id}\n"
                f"👤 Username: @{session.get('username', '—')}\n"
                f"⏰ Первый контакт: {session.get('first_seen', '—')}\n\n"
                f"{history_text}\n\n"
                f"{summary}"
            )

            bot.send_message(ADMIN_ID, admin_report, parse_mode="HTML")

            bot.send_message(
                chat_id,
                f"Спасибо, {name}! 🙏 Я передал данные менеджерам «КОКОС ТУР». "
                "Скоро с вами свяжутся 🌴"
            )

            del user_sessions[chat_id]
        return

    # Если анкеты нет — обычный ответ через ChatGPT
    reply = ask_gpt(text)
    session["history"].append(f"🤖 {reply}")
    bot.send_message(chat_id, reply)

print("✅ Бот «КОКОС ТУР» запущен и готов к работе!")
bot.polling(non_stop=True)
