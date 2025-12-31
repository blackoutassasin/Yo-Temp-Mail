import os, random, string, re
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import set_user_email, get_user_email, get_inbox, get_user_all_emails, delete_email
from dotenv import load_dotenv

load_dotenv()
bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))
DOMAIN = os.getenv("DOMAIN")

def gen_email():
    name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=7))
    return f"{name}@{DOMAIN}"

def get_main_panel(email):
    text = (
        f"📧 <b>Temporary Inbox</b>\n"
        f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n"
        f"📮 <b>Email:</b> <code>{email}</code>\n"
        f"<i>(Tap to copy address)</i>\n\n"
        f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬"
    )
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🔄 Refresh", callback_data="refresh"),
        InlineKeyboardButton("✨ New Address", callback_data="new_email")
    )
    markup.add(
        InlineKeyboardButton("📜 History", callback_data="history"),
        InlineKeyboardButton("🗑️ Delete Current", callback_data=f"del_{email}")
    )
    return text, markup

@bot.message_handler(commands=["start"])
def start(m):
    email = gen_email()
    set_user_email(m.chat.id, email)
    text, markup = get_main_panel(email)
    bot.send_message(m.chat.id, text, reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    chat_id = call.message.chat.id
    if call.data == "refresh":
        email = get_user_email(chat_id)
        inbox = get_inbox(email)
        if not inbox:
            bot.answer_callback_query(call.id, "📭 Inbox is empty!")
            return
        for s, sub, b, t in inbox:
            msg = (f"📨 <b>New Mail</b>\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n👤 <b>From:</b> {s}\n📌 <b>Sub:</b> {sub}\n\n{b[:3000]}")
            bot.send_message(chat_id, msg, parse_mode="HTML")
    elif call.data == "new_email":
        email = gen_email()
        set_user_email(chat_id, email)
        text, markup = get_main_panel(email)
        bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
    elif call.data == "history":
        emails = get_user_all_emails(chat_id)
        if emails:
            bot.send_message(chat_id, "📜 <b>Your Emails:</b>", parse_mode="HTML")
            for e in emails[:5]:
                m = InlineKeyboardMarkup().add(InlineKeyboardButton("✅ Activate", callback_data=f"set_{e}"))
                bot.send_message(chat_id, f"<code>{e}</code>", reply_markup=m, parse_mode="HTML")

bot.infinity_polling()
