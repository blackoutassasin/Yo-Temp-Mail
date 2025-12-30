import os, random, string, re
import telebot
from telebot.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from database import set_user_email, get_user_email, get_inbox, get_user_all_emails
from dotenv import load_dotenv

load_dotenv()

bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))
DOMAIN = os.getenv("DOMAIN")

def gen_email():
    name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=7))
    return f"{name}@{DOMAIN}"

# লিঙ্ক বের করা এবং কোড বোল্ড করার ফাংশন
def extract_links(text):
    return re.findall(r'(https?://\S+)', text)

def bold_codes(text):
    return re.sub(r'\b(\d{4,8})\b', r'*\1*', text)

def keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📧 Generate New Email", "📨 My Email History")
    kb.add("🔄 Refresh Inbox")
    return kb

@bot.message_handler(commands=["start"])
def start(m):
    email = gen_email()
    set_user_email(m.chat.id, email)
    bot.send_message(
        m.chat.id,
        f"👋 *Yo-Temp-Mail Bot*\n\n📮 *Active Email:* `{email}`",
        reply_markup=keyboard(),
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda m: m.text == "📧 Generate New Email")
def new_email(m):
    email = gen_email()
    set_user_email(m.chat.id, email)
    bot.send_message(m.chat.id, f"✅ *New Email:* `{email}`", parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "📨 My Email History")
def show_history(m):
    emails = get_user_all_emails(m.chat.id)
    
    if not emails:
        current = get_user_email(m.chat.id)
        bot.send_message(m.chat.id, f"📍 *Current:* `{current}`\n(No history found)")
        return

    markup = InlineKeyboardMarkup()
    for email in emails:
        markup.add(InlineKeyboardButton(text=f"📧 {email}", callback_data=f"set_{email}"))
    
    bot.send_message(m.chat.id, "📜 *Last 50 Emails:*\nClick to activate an old address.", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith('set_'))
def handle_set_email(call):
    selected = call.data.split('_')[1]
    set_user_email(call.message.chat.id, selected)
    bot.answer_callback_query(call.id, f"Activated: {selected}")
    bot.edit_message_text(f"✅ *Active Email Changed!*\n📮 `{selected}`", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "🔄 Refresh Inbox")
def refresh(m):
    email = get_user_email(m.chat.id)
    inbox = get_inbox(email)
    
    if not inbox:
        bot.send_message(m.chat.id, "📭 *Inbox Empty*")
        return

    for sender, subject, body, time in inbox:
        formatted_body = bold_codes(body)
        links = extract_links(body)
        
        text = (f"👤 *From:* {sender}\n📌 *Subject:* {subject}\n🕒 *Time:* {time}\n\n"
                f"📝 *Message:* \n{formatted_body}")
        
        markup = InlineKeyboardMarkup()
        if links:
            for i, link in enumerate(links[:3]):
                markup.add(InlineKeyboardButton(text=f"🔗 Link {i+1}", url=link))
        
        bot.send_message(m.chat.id, text[:4096], reply_markup=markup, parse_mode="Markdown")

bot.infinity_polling()
