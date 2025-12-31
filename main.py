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

def extract_links(text):
    return re.findall(r'(https?://\S+)', text)

# প্রফেশনাল মেইন প্যানেল জেনারেটর
def get_main_panel(email):
    text = (
        f"📧 <b>Your Temporary Inbox</b>\n"
        f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n"
        f"📮 <b>Email:</b> <code>{email}</code>\n"
        f"<i>(Tap to copy address)</i>\n\n"
        f"🕒 <b>Status:</b> Listening for emails...\n"
        f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬"
    )
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🔄 Refresh Inbox", callback_data="refresh"),
        InlineKeyboardButton("✨ New Address", callback_data="new_email")
    )
    markup.add(
        InlineKeyboardButton("📜 History", callback_data="history"),
        InlineKeyboardButton("🗑️ Delete", callback_data=f"del_{email}")
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
    data = call.data

    if data == "refresh":
        email = get_user_email(chat_id)
        inbox = get_inbox(email)
        if not inbox:
            bot.answer_callback_query(call.id, "📭 Inbox is empty!")
            return
        
        bot.answer_callback_query(call.id, "✅ Loading messages...")
        for sender, subject, body, time in inbox:
            msg_text = (
                f"📨 <b>MESSAGE RECEIVED</b>\n"
                f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
                f"👤 <b>From:</b> <code>{sender}</code>\n"
                f"📌 <b>Subject:</b> {subject}\n"
                f"🕒 <b>Time:</b> {time}\n"
                f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n"
                f"📝 <b>Body:</b>\n{body[:3000]}"
            )
            links = extract_links(body)
            markup = InlineKeyboardMarkup()
            if links:
                for i, link in enumerate(links[:3]):
                    markup.add(InlineKeyboardButton(text=f"🔗 Link {i+1}", url=link))
            bot.send_message(chat_id, msg_text, reply_markup=markup, parse_mode="HTML")

    elif data == "new_email":
        email = gen_email()
        set_user_email(chat_id, email)
        text, markup = get_main_panel(email)
        bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

    elif data == "history":
        emails = get_user_all_emails(chat_id)
        if not emails:
            bot.answer_callback_query(call.id, "❌ No history found!")
            return
        
        bot.send_message(chat_id, "<b>📜 Your Last Emails:</b>", parse_mode="HTML")
        for email in emails[:10]:
            markup = InlineKeyboardMarkup()
            markup.add(
                InlineKeyboardButton("✅ Activate", callback_data=f"set_{email}"),
                InlineKeyboardButton("🗑️ Delete", callback_data=f"del_{email}")
            )
            bot.send_message(chat_id, f"📧 <code>{email}</code>", reply_markup=markup, parse_mode="HTML")

    elif data.startswith('set_'):
        email = data.split('_')[1]
        set_user_email(chat_id, email)
        text, markup = get_main_panel(email)
        bot.send_message(chat_id, "✅ <b>Email Activated!</b>", parse_mode="HTML")
        bot.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")

    elif data.startswith('del_'):
        email = data.split('_')[1]
        delete_email(chat_id, email)
        bot.answer_callback_query(call.id, "🗑️ Deleted!", show_alert=True)
        bot.delete_message(chat_id, call.message.message_id)

bot.infinity_polling()
