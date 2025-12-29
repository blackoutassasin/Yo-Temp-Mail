import os
from flask import Flask, request, jsonify
from database import save_email
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
SECRET = os.getenv("API_SECRET")

@app.route("/email", methods=["POST"])
def email():
    data = request.json

    if data.get("secret") != SECRET:
        return jsonify({"error": "forbidden"}), 403

    save_email(
        data["to"],
        data["from"],
        data["subject"],
        data["body"]
    )
    return jsonify({"ok": True})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

