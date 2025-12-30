# database.py ফাইলে এই অংশটুকু আপডেট করুন
import sqlite3
import os

conn = sqlite3.connect("tempmail.db", check_same_thread=False)
cur = conn.cursor()

# হিস্টোরি রাখার জন্য নতুন টেবিল (যদি না থাকে)
cur.execute("""
CREATE TABLE IF NOT EXISTS email_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER,
    email TEXT,
    UNIQUE(telegram_id, email)
)
""")
conn.commit()

def set_user_email(tg_id, email):
    # বর্তমান মেইল সেট করা
    cur.execute("INSERT OR REPLACE INTO users (telegram_id, email) VALUES (?,?)", (tg_id, email))
    # হিস্টোরি টেবিলে মেইলটি যোগ করা
    cur.execute("INSERT OR IGNORE INTO email_history (telegram_id, email) VALUES (?,?)", (tg_id, email))
    conn.commit()

def get_user_all_emails(tg_id):
    # এখন আমরা সরাসরি হিস্টোরি টেবিল থেকে শেষ ৫০টি মেইল আনবো
    cur.execute("SELECT email FROM email_history WHERE telegram_id=? ORDER BY id DESC LIMIT 50", (tg_id,))
    return [r[0] for r in cur.fetchall()]
