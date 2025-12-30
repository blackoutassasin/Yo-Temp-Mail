import os, random, string, re
import telebot
from telebot.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from database import set_user_email, get_user_email, get_inbox
from dotenv import load_dotenv

load_dotenv()

bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))
DOMAIN = os.getenv("DOMAIN")
ADMIN_ID = os.getenv("ADMIN_ID")

def gen_email():
    name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=7))
    return f"{name}@{DOMAIN}"

# লিঙ্ক খুঁজে বের করার ফাংশন
def extract_links(text):
    return re.findall(r'(https?://\S+)', text)

# ওটিপি/কোড বোল্ড করার ফাংশন
def bold_codes(text):
    # ৪ থেকে ৮ ডিজিটের নম্বর বোল্ড করবে
    return re.sub(r'\b(\d{4,8})\b', r'*\1*', text)

def keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📧 Generate New Email", "📨 My Email")
    kb.add("🔄 Refresh Inbox")
    return kb

@bot.message_handler(commands=["start"])
def start(m):
    email = gen_email()
    set_user_email(m.chat.id, email)
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📋 Copy Email", callback_data=f"copy_{email}"))
    
    bot.send_message(
        m.chat.id,
        f"👋 *Yo-Temp-Mail Bot*\n\n"
        f"Your temporary email address is ready!\n\n"
        f"📮 *Address:* `{email}`\n\n"
        f"মেইল আসার পর নিচের *Refresh* বাটনে ক্লিক করুন।",
        reply_markup=keyboard(),
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda m: m.text == "📧 Generate New Email")
def new_email(m):
    email = gen_email()
    set_user_email(m.chat.id, email)
    bot.send_message(m.chat.id, f"✅ *New Email Generated:*\n`{email}`", parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "📨 My Email")
def my_email(m):
    email = get_user_email(m.chat.id)
    if email:
        bot.send_message(m.chat.id, f"📮 *Your Current Email:*\n`{email}`", parse_mode="Markdown")
    else:
        bot.send_message(m.chat.id, "❌ No email found. Click 'Generate' to get one.")

@bot.message_handler(func=lambda m: m.text == "🔄 Refresh Inbox")
def refresh(m):
    email = get_user_email(m.chat.id)
    inbox = get_inbox(email)
    
    if not inbox:
        bot.send_message(m.chat.id, "📭 *Inbox is empty!*\n(মেইল পাঠানোর পর ১-৫ সেকেন্ড অপেক্ষা করুন)")
        return

    for msg in inbox:
        sender, subject, body, time = msg
        
        # কোড বোল্ড করা
        formatted_body = bold_codes(body)
        # লিঙ্ক বের করা
        links = extract_links(body)
        
        text = (f"📧 *From:* {sender}\n"
                f"📝 *Subject:* {subject}\n"
                f"📅 *Time:* {time}\n"
                f"━━━━━━━━━━━━━━━\n"
                f"💬 *Message:* \n{formatted_body}")
        
        markup = InlineKeyboardMarkup()
        if links:
            # প্রথম ৩টি ক্লিকেবল লিঙ্ক বাটন হিসেবে দেখাবে
            for i, link in enumerate(links[:3]):
                markup.add(InlineKeyboardButton(text=f"🔗 Verification Link {i+1}", url=link))
        
        try:
            bot.send_message(m.chat.id, text, reply_markup=markup, parse_mode="Markdown")
        except:
            # মেইল খুব বড় হলে ট্রিম করে পাঠানো
            bot.send_message(m.chat.id, text[:3900] + "\n\n...(Message too long)", reply_markup=markup, parse_mode="Markdown")

# টেক্সট কপি করার জন্য কলব্যাক (ঐচ্ছিক ফিচার)
@bot.callback_query_handler(func=lambda call: call.data.startswith('copy_'))
def copy_email(call):
    email = call.data.split('_')[1]
    bot.answer_callback_query(call.id, f"Email Copied: {email}", show_alert=True)

if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling()
