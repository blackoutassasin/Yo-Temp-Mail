import os
import telebot
from flask import Flask, request, jsonify
from database import save_email, get_tg_id_by_email
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))
SECRET = os.getenv("API_SECRET")

@app.route("/email", methods=["POST"])
def email():
    data = request.json
    if data.get("secret") != SECRET:
        return jsonify({"error": "forbidden"}), 403

    email_to = data["to"]
    save_email(email_to, data["from"], data["subject"], data["body"])

    # নতুন মেইল আসলে ইউজারকে মেসেজ পাঠানো
    tg_id = get_tg_id_by_email(email_to)
    if tg_id:
        text = (f"🔔 <b>New Mail Received!</b>\n"
                f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
                f"👤 <b>From:</b> {data['from']}\n"
                f"📌 <b>Subject:</b> {data['subject']}\n"
                f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬")
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("📥 View Inbox", callback_data="refresh"))
        bot.send_message(tg_id, text, parse_mode="HTML", reply_markup=markup)

    return jsonify({"ok": True})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
