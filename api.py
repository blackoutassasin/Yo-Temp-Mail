import os, html, re
import telebot
from flask import Flask, request, jsonify
from database import save_email, get_tg_id_by_email
from dotenv import load_dotenv

load_dotenv()
app   = Flask(__name__)
bot   = telebot.TeleBot(os.getenv("BOT_TOKEN"))
SECRET = os.getenv("API_SECRET", "")


def strip_html(text: str) -> str:
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
    max_len = 4000
    if len(text) <= max_len:
        bot.send_message(chat_id, text, parse_mode=parse_mode, **kwargs)
    else:
        parts = [text[i:i+max_len] for i in range(0, len(text), max_len)]
        for i, part in enumerate(parts):
            extra = kwargs if i == len(parts) - 1 else {}
            bot.send_message(chat_id, part, parse_mode=parse_mode, **extra)


@app.route("/", methods=["GET"])
def index():
    return jsonify({"status": "Yo-TempMail API is running ✅"})


@app.route("/email", methods=["POST"])
def receive_email():
    data = request.json
    if not data:
        return jsonify({"error": "no data"}), 400

    # Validate secret
    if SECRET and data.get("secret") != SECRET:
        return jsonify({"error": "forbidden"}), 403

    email_to = data.get("to", "")
    sender   = data.get("from", "unknown")
    subject  = data.get("subject", "(no subject)")
    body     = data.get("body", "")

    # Save to DB
    save_email(email_to, sender, subject, body)

    # Notify user on Telegram
    tg_id = get_tg_id_by_email(email_to)
    if tg_id:
        clean_body = strip_html(body)

        header = (
            f"🔔 <b>New Message Received!</b>\n"
            f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
            f"👤 <b>From:</b> {html.escape(str(sender))}\n"
            f"📌 <b>Subject:</b> {html.escape(str(subject))}\n"
            f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n"
        )

        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("📥 View All Inbox", callback_data="refresh"))

        full_message = header + html.escape(clean_body)
        send_chunks(tg_id, full_message, parse_mode="HTML", reply_markup=markup)

    return jsonify({"ok": True})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
