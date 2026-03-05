import os, random, string, html, re
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import (set_user_email, get_user_email, get_inbox,
                      get_user_all_emails, delete_email_address,
                      delete_single_mail, get_email_by_id)
from dotenv import load_dotenv

load_dotenv()
bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))
DOMAIN = os.getenv("DOMAIN", "yourdomain.com")


# ── Helpers ──────────────────────────────────────────────────────────────────
def gen_email():
    name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{name}@{DOMAIN}"


def strip_html(text: str) -> str:
    """Remove HTML tags and clean up whitespace."""
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<p[^>]*>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</p>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<[^>]+>', '', text)
    text = html.unescape(text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def send_chunks(chat_id, text, parse_mode="HTML", **kwargs):
    """Send message in 4000-char chunks to respect Telegram's limit."""
    max_len = 4000
    if len(text) <= max_len:
        bot.send_message(chat_id, text, parse_mode=parse_mode, **kwargs)
    else:
        parts = [text[i:i+max_len] for i in range(0, len(text), max_len)]
        for i, part in enumerate(parts):
            extra = kwargs if i == len(parts) - 1 else {}
            bot.send_message(chat_id, part, parse_mode=parse_mode, **extra)


def get_main_panel(email):
    text = (
        f"📧 <b>Temporary Inbox</b>\n"
        f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n"
        f"📮 <b>Email:</b> <code>{html.escape(email)}</code>\n"
        f"<i>Tap the address above to copy it</i>\n\n"
        f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬"
    )
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🔄 Refresh Inbox", callback_data="refresh"),
        InlineKeyboardButton("✨ New Address",   callback_data="new_email"),
    )
    markup.add(
        InlineKeyboardButton("📜 History",          callback_data="history"),
        InlineKeyboardButton("🗑️ Delete Address",   callback_data=f"del_{email}"),
    )
    return text, markup


# ── Handlers ──────────────────────────────────────────────────────────────────
@bot.message_handler(commands=["start"])
def start(m):
    email = gen_email()
    set_user_email(m.chat.id, email)
    text, markup = get_main_panel(email)
    bot.send_message(m.chat.id, text, reply_markup=markup, parse_mode="HTML")


@bot.message_handler(commands=["inbox"])
def cmd_inbox(m):
    email = get_user_email(m.chat.id)
    if not email:
        bot.send_message(m.chat.id, "⚠️ No email assigned. Use /start first.")
        return
    show_inbox(m.chat.id, email)


def show_inbox(chat_id, email):
    inbox = get_inbox(email)
    if not inbox:
        bot.send_message(chat_id, "📭 <b>Inbox is empty!</b>\n\nWaiting for new messages…", parse_mode="HTML")
        return
    for mail_id, sender, subject, body, time in inbox:
        send_mail_message(chat_id, mail_id, sender, subject, body, time)


def send_mail_message(chat_id, mail_id, sender, subject, body, time=None):
    clean = strip_html(body)
    safe_sender  = html.escape(str(sender))
    safe_subject = html.escape(str(subject))
    safe_time    = html.escape(str(time)) if time else ""

    header = (
        f"📨 <b>New Mail</b>\n"
        f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        f"👤 <b>From:</b> {safe_sender}\n"
        f"📌 <b>Subject:</b> {safe_subject}\n"
        f"🕐 <b>Time:</b> {safe_time}\n"
        f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n"
    )

    del_markup = InlineKeyboardMarkup()
    del_markup.add(InlineKeyboardButton("🗑️ Delete this mail", callback_data=f"delmail_{mail_id}"))

    full_text = header + html.escape(clean)
    send_chunks(chat_id, full_text, parse_mode="HTML", reply_markup=del_markup)


@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    chat_id = call.message.chat.id
    data    = call.data

    # ── Refresh ──────────────────────────────────────────────────────────────
    if data == "refresh":
        email = get_user_email(chat_id)
        if not email:
            bot.answer_callback_query(call.id, "⚠️ No email set. Use /start.")
            return
        inbox = get_inbox(email)
        if not inbox:
            bot.answer_callback_query(call.id, "📭 Inbox is empty!", show_alert=True)
            return
        bot.answer_callback_query(call.id, f"📬 {len(inbox)} message(s) found!")
        for mail_id, sender, subject, body, time in inbox:
            send_mail_message(chat_id, mail_id, sender, subject, body, time)

    # ── New email ─────────────────────────────────────────────────────────────
    elif data == "new_email":
        email = gen_email()
        set_user_email(chat_id, email)
        text, markup = get_main_panel(email)
        try:
            bot.edit_message_text(text, chat_id, call.message.message_id,
                                  reply_markup=markup, parse_mode="HTML")
        except Exception:
            bot.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")
        bot.answer_callback_query(call.id, "✅ New address created!")

    # ── History ───────────────────────────────────────────────────────────────
    elif data == "history":
        emails = get_user_all_emails(chat_id)
        if not emails:
            bot.answer_callback_query(call.id, "📭 No email history yet.", show_alert=True)
            return
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, "📜 <b>Your Email History:</b>", parse_mode="HTML")
        for e in emails[:10]:
            m = InlineKeyboardMarkup(row_width=2)
            m.add(
                InlineKeyboardButton("✅ Activate", callback_data=f"set_{e}"),
                InlineKeyboardButton("🗑️ Remove",   callback_data=f"del_{e}"),
            )
            bot.send_message(chat_id, f"<code>{html.escape(e)}</code>", reply_markup=m, parse_mode="HTML")

    # ── Activate email from history ───────────────────────────────────────────
    elif data.startswith("set_"):
        email = data[4:]
        set_user_email(chat_id, email)
        text, markup = get_main_panel(email)
        bot.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")
        bot.answer_callback_query(call.id, f"✅ Switched to {email}")

    # ── Delete email address ──────────────────────────────────────────────────
    elif data.startswith("del_"):
        email = data[4:]
        delete_email_address(chat_id, email)
        bot.answer_callback_query(call.id, "🗑️ Address deleted!", show_alert=True)
        # Generate a fresh one
        new_email = gen_email()
        set_user_email(chat_id, new_email)
        text, markup = get_main_panel(new_email)
        try:
            bot.edit_message_text(text, chat_id, call.message.message_id,
                                  reply_markup=markup, parse_mode="HTML")
        except Exception:
            bot.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")

    # ── Delete individual mail ─────────────────────────────────────────────────
    elif data.startswith("delmail_"):
        mail_id = int(data[8:])
        delete_single_mail(mail_id)
        try:
            bot.delete_message(chat_id, call.message.message_id)
        except Exception:
            pass
        bot.answer_callback_query(call.id, "🗑️ Mail deleted!")

    else:
        bot.answer_callback_query(call.id)


if __name__ == "__main__":
    print("🤖 Bot is running…")
    bot.infinity_polling(timeout=60, long_polling_timeout=60)
