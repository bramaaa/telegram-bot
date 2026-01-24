import telebot

TOKEN = "8319404629:AAGf6lGu4hQ_jteb0tq_5w02DSgzb1q2KLY"
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Вітаю! Очікуйте розклад. Якщо ви вам потрібен бот - пишіть @bramaaaaaa")


bot.infinity_polling(none_stop=True)
