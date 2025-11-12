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

# 🔹 Укажи свой Telegram ID (узнай у @userinfobot)
ADMIN_ID = 7928610544  # 👈 замени на свой ID

# 🔹 Память пользователей
user_sessions = {}

# 🔹 Вопросы анкеты
questions = [
    "Как вас зовут? 😊",
    "Пожалуйста, укажите номер телефона, чтобы менеджер мог связаться с вами 📱",
    "Куда вы хотите отправиться? 🌴",
    "На сколько человек планируете поездку?",
    "На сколько дней хотите отдохнуть?",
    "Какие даты вылета вас интересуют? 📅"
]

# --- 🔸 ChatGPT функция с контекстом ---
def ask_gpt(chat_id, prompt):
    """ChatGPT теперь помнит историю общения пользователя."""
    try:
        session = user_sessions.setdefault(chat_id, {"history": []})

        # Ограничиваем длину истории (чтобы не перегружать запрос)
        history = session["history"][-6:]  # последние 6 сообщений

        messages = [
            {
                "role": "system",
                "content": (
                    "Ты — дружелюбный и профессиональный ассистент туристического агентства "
                    "«КОКОС ТУР». Общайся естественно, не начинай каждое сообщение с приветствия, "
                    "если диалог уже идёт. Помогаешь клиентам подобрать отдых, туры, отели и визы. "
                    "Отвечай от имени компании «КОКОС ТУР» — пиши вежливо, позитивно и уверенно. "
                    "Если вопрос не по теме туризма — оставайся дружелюбным и напомни, что "
                    "по вопросам бронирования можно обращаться к менеджерам: Малик (+998774127752) "
                    "и Владислав (+998971779848)."
                )
            }
        ]

        # Добавляем предыдущие реплики
        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})

        # Добавляем текущее сообщение
        messages.append({"role": "user", "content": prompt})

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )

        reply = response.choices[0].message.content.strip()

        # Сохраняем в историю
        session["history"].append({"role": "user", "content": prompt})
        session["history"].append({"role": "assistant", "content": reply})

        return reply

    except Exception as e:
        return f"Ошибка: {e}"

# --- 🔸 /start ---
@bot.message_handler(commands=["start"])
def start(message):
    chat_id = message.chat.id
    user = message.from_user
    username = user.username or "—"

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

    # Сообщаем админу о новом пользователе
    bot.send_message(
        ADMIN_ID,
        f"📨 Новый пользователь обратился к боту:\n\n"
        f"🧍‍♂️ Имя: {user.first_name or '—'}\n"
        f"👤 Username: @{username}\n"
        f"🆔 ID: {chat_id}\n"
        f"⏰ Время: {user_sessions[chat_id]['first_seen']}\n\n"
        f"💬 Стартовал диалог с ботом «КОКОС ТУР» 🌴"
    )

# --- 🔸 Обработка всех сообщений ---
@bot.message_handler(func=lambda msg: True)
def handle_message(message):
    chat_id = message.chat.id
    text = message.text.strip()

    session = user_sessions.setdefault(chat_id, {"history": []})
    session["history"].append({"role": "user", "content": text})

    # Проверяем, идёт ли анкета
    if "step" in session and session["step"] < len(questions):
        step = session["step"]
        data = session["data"]
        data[f"q{step}"] = text
        session["step"] += 1

        if session["step"] < len(questions):
            bot.send_message(chat_id, questions[session["step"]])
        else:
            # Анкета завершена — формируем заявку
            name = data.get("q0", "—")
            phone = data.get("q1", "—")
            destination = data.get("q2", "—")
            people = data.get("q3", "—")
            days = data.get("q4", "—")
            dates = data.get("q5", "—")

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

            # Отправляем админу
            history_text = "\n".join(
                [f"👤 {m['content']}" for m in session["history"][-8:]]
            )
            admin_report = (
                f"📬 <b>История общения с пользователем:</b>\n"
                f"👤 Username: @{session.get('username', '—')}\n"
                f"🕒 Первый контакт: {session.get('first_seen', '—')}\n\n"
                f"{history_text}\n\n{summary}"
            )

            bot.send_message(ADMIN_ID, admin_report, parse_mode="HTML")
            bot.send_message(
                chat_id,
                f"Спасибо, {name}! 🙏 Я передал данные менеджерам «КОКОС ТУР». "
                "Скоро с вами свяжутся 🌴"
            )

            del user_sessions[chat_id]
        return

    # Обычный ответ через ChatGPT с контекстом
    reply = ask_gpt(chat_id, text)
    bot.send_message(chat_id, reply)

print("✅ Бот «КОКОС ТУР» запущен и готов к работе!")
bot.polling(non_stop=True)