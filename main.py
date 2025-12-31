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
    text = (f"📧 <b>Temporary Inbox</b>\n"
            f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n"
            f"📮 <b>Email:</b> <code>{email}</code>\n"
            f"<i>(Tap to copy)</i>\n\n"
            f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬")
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(InlineKeyboardButton("🔄 Refresh", callback_data="refresh"),
               InlineKeyboardButton("✨ New Email", callback_data="new_email"))
    markup.add(InlineKeyboardButton("📜 History", callback_data="history"),
               InlineKeyboardButton("🗑️ Delete", callback_data=f"del_{email}"))
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
            bot.answer_callback_query(call.id, "📭 Inbox empty!")
            return
        bot.answer_callback_query(call.id, "✅ Checking...")
        for s, sub, b, t in inbox:
            bot.send_message(chat_id, f"👤 <b>From:</b> {s}\n📌 <b>Subject:</b> {sub}\n\n📝 <b>Body:</b>\n{b[:3000]}", parse_mode="HTML")

    elif call.data == "new_email":
        email = gen_email()
        set_user_email(chat_id, email)
        text, markup = get_main_panel(email)
        bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

    elif call.data == "history":
        emails = get_user_all_emails(chat_id)
        if not emails:
            bot.answer_callback_query(call.id, "❌ No history!")
            return
        for email in emails[:5]:
            m = InlineKeyboardMarkup().add(InlineKeyboardButton("✅ Set Active", callback_data=f"set_{email}"))
            bot.send_message(chat_id, f"📧 <code>{email}</code>", reply_markup=m, parse_mode="HTML")

    elif call.data.startswith('set_'):
        email = call.data.split('_')[1]
        set_user_email(chat_id, email)
        text, markup = get_main_panel(email)
        bot.send_message(chat_id, "✅ <b>Activated!</b>", parse_mode="HTML")
        bot.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")

bot.infinity_polling()
