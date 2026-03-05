"""
Entry point for Railway.
Runs Flask API (api.py) and Telegram bot (main.py) in the same process.
"""
import threading
import os

def run_api():
    from api import app
    port = int(os.environ.get("PORT", 8080))
    print(f"🌐 Flask API starting on port {port}…")
    app.run(host="0.0.0.0", port=port)

def run_bot():
    from main import bot
    print("🤖 Telegram Bot starting…")
    bot.infinity_polling(timeout=60, long_polling_timeout=60)

if __name__ == "__main__":
    api_thread = threading.Thread(target=run_api, daemon=True)
    api_thread.start()

    # Bot runs in main thread
    run_bot()
