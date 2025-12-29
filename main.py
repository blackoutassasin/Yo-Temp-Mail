import os, random, string
import telebot
from telebot.types import ReplyKeyboardMarkup
from database import set_user_email, get_user_email, get_inbox
from dotenv import load_dotenv

load_dotenv()

bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))
DOMAIN = os.getenv("DOMAIN")

def gen_email():
    name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=7))
    return f"{name}@{DOMAIN}"

def keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📧 Generate New Email", "📨 My Email")
    kb.add("🔄 Refresh Inbox")
    return kb

@bot.message_handler(commands=["start"])
def start(m):
    email = gen_email()
    set_user_email(m.chat.id, email)
    bot.send_message(
        m.chat.id,
        f"👋 *Temp Mail Bot*\n\n"
        f"📮 *Your Email:*\n`{email}`",
        reply_markup=keyboard(),
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda m: m.text == "📧 Generate New Email")
def new_email(m):
    email = gen_email()
    set_user_email(m.chat.id, email)
    bot.send_message(m.chat.id, f"✅ New Email:\n`{email}`", parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "📨 My Email")
def my_email(m):
    email = get_user_email(m.chat.id)
    bot.send_message(m.chat.id, f"📮 Your Email:\n`{email}`", parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "🔄 Refresh Inbox")
def refresh(m):
    email = get_user_email(m.chat.id)
    inbox = get_inbox(email)

    if not inbox:
        bot.send_message(m.chat.id, "📭 Inbox Empty")
        return

    text = "📬 *Inbox*\n\n"
    for s, sub, body, t in inbox:
        text += f"👤 From: {s}\n📌 Subject: {sub}\n📝 {body[:200]}\n🕒 {t}\n\n"

    bot.send_message(m.chat.id, text, parse_mode="Markdown")

bot.infinity_polling()

