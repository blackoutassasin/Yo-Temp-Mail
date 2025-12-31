import sqlite3
import os

conn = sqlite3.connect("tempmail.db", check_same_thread=False)
cur = conn.cursor()

# টেবিল তৈরি
cur.execute("CREATE TABLE IF NOT EXISTS users (telegram_id INTEGER PRIMARY KEY, email TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS inbox (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT, sender TEXT, subject TEXT, body TEXT, time DATETIME DEFAULT CURRENT_TIMESTAMP)")
cur.execute("CREATE TABLE IF NOT EXISTS email_history (id INTEGER PRIMARY KEY AUTOINCREMENT, telegram_id INTEGER, email TEXT, UNIQUE(telegram_id, email))")
conn.commit()

def set_user_email(tg_id, email):
    cur.execute("REPLACE INTO users VALUES (?,?)", (tg_id, email))
    # নিচের লাইনটি থেকে \ চিহ্নটি সরানো হয়েছে যা আপনার এরর এর মূল কারণ ছিল
    cur.execute("INSERT OR IGNORE INTO email_history (telegram_id, email) VALUES (?,?)", (tg_id, email))
    conn.commit()

def get_user_email(tg_id):
    cur.execute("SELECT email FROM users WHERE telegram_id=?", (tg_id,))
    r = cur.fetchone()
    return r[0] if r else None

def get_tg_id_by_email(email):
    cur.execute("SELECT telegram_id FROM users WHERE email=?", (email,))
    r = cur.fetchone()
    return r[0] if r else None

def save_email(email, sender, subject, body):
    cur.execute("INSERT INTO inbox (email,sender,subject,body) VALUES (?,?,?,?)", (email, sender, subject, body))
    conn.commit()

def get_inbox(email):
    cur.execute("SELECT sender,subject,body,time FROM inbox WHERE email=? ORDER BY id DESC LIMIT 10", (email,))
    return cur.fetchall()

def get_user_all_emails(tg_id):
    cur.execute("SELECT email FROM email_history WHERE telegram_id=? ORDER BY id DESC LIMIT 50", (tg_id,))
    return [r[0] for r in cur.fetchall()]

def delete_email(tg_id, email):
    cur.execute("DELETE FROM email_history WHERE telegram_id=? AND email=?", (tg_id, email))
    cur.execute("DELETE FROM inbox WHERE email=?", (email,))
    cur.execute("DELETE FROM users WHERE telegram_id=? AND email=?", (tg_id, email))
    conn.commit()
