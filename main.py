import telebot
import os
import json
import schedule
import pytz
import threading
import time
from datetime import datetime


TOKEN = "8548025603:AAHMZH14AHS0aAHI4fOIvby2_0kneknM-G0"
ADMIN_PASSWORD = 568130284183
DATA_FILE = "users.json"
TIMEZONE = "Europe/Kyiv"


bot = telebot.TeleBot(TOKEN)
admins = set()


def load_users():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


def save_users(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def find_by_name(name):
    users = load_users()
    for uid, data in users.items():
        if data.get("name", "").lower() == name.lower():
            return uid
    return None



@bot.message_handler(commands=["start"])
def start(message):
    users = load_users()
    uid = str(message.chat.id)

    if uid in users:
        name = users[uid]["name"]
        schedule_text = users[uid]["schedule"]
        bot.send_message(
            message.chat.id,
            f"👋 {name}\n\n📅 Твій розклад:\n{schedule_text}"
        )
    else:
        bot.send_message(
            message.chat.id,
            "❌ Тебе ще немає в базі.\nЗвернись до адміністратора."
        )



@bot.message_handler(commands=["admin"])
def admin_login(message):
    msg = bot.send_message(message.chat.id, "🔐 Введи пароль адміністратора:")
    bot.register_next_step_handler(msg, check_password)


def check_password(message):
    if message.text == ADMIN_PASSWORD:
        admins.add(message.chat.id)
        bot.send_message(
            message.chat.id,
            "✅ Ти адмін!\n\n"
            "📌 Команди:\n"
            "/setname ID Ім'я\n"
            "/set Ім'я Розклад\n"
            "/del Ім'я\n"
            "/list\n"
            "/sendnow"
        )
    else:
        bot.send_message(message.chat.id, "❌ Невірний пароль")



@bot.message_handler(commands=["setname"])
def set_name(message):
    if message.chat.id not in admins:
        return

    try:
        _, user_id, name = message.text.split(maxsplit=2)
        users = load_users()

        users[user_id] = users.get(user_id, {})
        users[user_id]["name"] = name
        users[user_id].setdefault("schedule", "")

        save_users(users)
        bot.send_message(message.chat.id, f"✅ Ім'я збережено: {name}")
    except:
        bot.send_message(
            message.chat.id,
            "❗ Формат:\n/setname 123456789 Ім'я"
        )



@bot.message_handler(commands=["set"])
def set_schedule(message):
    if message.chat.id not in admins:
        return

    try:
        _, name, *text = message.text.split()
        schedule_text = " ".join(text)

        users = load_users()
        uid = find_by_name(name)

        if not uid:
            bot.send_message(message.chat.id, "❌ Ім'я не знайдено")
            return

        users[uid]["schedule"] = schedule_text
        save_users(users)

        bot.send_message(
            message.chat.id,
            f"✅ Розклад оновлено для {name}"
        )
    except:
        bot.send_message(
            message.chat.id,
            "❗ Формат:\n/set Ім'я Понеділок - 15:00"
        )



@bot.message_handler(commands=["del"])
def delete_user(message):
    if message.chat.id not in admins:
        return

    try:
        name = message.text.split(maxsplit=1)[1]
        users = load_users()
        uid = find_by_name(name)

        if uid:
            del users[uid]
            save_users(users)
            bot.send_message(message.chat.id, "🗑 Видалено")
        else:
            bot.send_message(message.chat.id, "❌ Ім'я не знайдено")
    except:
        bot.send_message(message.chat.id, "Формат: /del Ім'я")



@bot.message_handler(commands=["list"])
def list_users(message):
    if message.chat.id not in admins:
        return

    users = load_users()
    if not users:
        bot.send_message(message.chat.id, "📭 Список порожній")
        return

    text = ""
    for uid, data in users.items():
        text += f"👤 {data['name']} ({uid})\n📅 {data['schedule']}\n\n"

    bot.send_message(message.chat.id, text)



def send_weekly_schedule():
    users = load_users()
    kyiv = pytz.timezone(TIMEZONE)
    now = datetime.now(kyiv).strftime("%d.%m %H:%M")

    for uid, data in users.items():
        try:
            bot.send_message(
                uid,
                f"📅 Розклад на тиждень\n"
                f"🕗 {now}\n\n"
                f"{data['name']}, твій розклад:\n"
                f"{data['schedule']}"
            )
        except Exception as e:
            print(f"Не вдалося надіслати {uid}: {e}")



@bot.message_handler(commands=["sendnow"])
def send_now(message):
    if message.chat.id not in admins:
        return

    send_weekly_schedule()
    bot.send_message(message.chat.id, "✅ Розсилка виконана")



def scheduler():
    schedule.every().sunday.at("10:00").do(send_weekly_schedule)

    while True:
        schedule.run_pending()
        time.sleep(30)


threading.Thread(target=scheduler, daemon=True).start()
bot.infinity_polling()
