import telebot
from telebot.types import KeyboardButton, ReplyKeyboardMarkup
from dotenv import load_dotenv
import os
from chatbot import replybot

load_dotenv()
telegram_token = os.getenv("TELEGRAM_TOKEN")

print("token: ", telegram_token)

bot = telebot.TeleBot(telegram_token)


# Definir un gestor de mensajes para los comandos /start y /help.
@bot.message_handler(commands=["start", "help"])
def send_welcome(message):
    bot.reply_to(
        message,
        """
        Hola, soy un bot de un centro de belleza. Esto es un TEST.
        """,
    ) 

@bot.message_handler(content_types=["text"])
def reply(message):
    replybot(bot, message)

bot.polling()