import sqlite3

conn = sqlite3.connect("tempmail.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    telegram_id INTEGER PRIMARY KEY,
    email TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS inbox (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT,
    sender TEXT,
    subject TEXT,
    body TEXT,
    time DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()

def set_user_email(tg_id, email):
    cur.execute("REPLACE INTO users VALUES (?,?)", (tg_id, email))
    conn.commit()

def get_user_email(tg_id):
    cur.execute("SELECT email FROM users WHERE telegram_id=?", (tg_id,))
    r = cur.fetchone()
    return r[0] if r else None

def save_email(email, sender, subject, body):
    cur.execute(
        "INSERT INTO inbox (email,sender,subject,body) VALUES (?,?,?,?)",
        (email, sender, subject, body)
    )
    conn.commit()

def get_inbox(email):
    cur.execute(
        "SELECT sender,subject,body,time FROM inbox WHERE email=? ORDER BY id DESC LIMIT 5",
        (email,)
    )
    return cur.fetchall()

