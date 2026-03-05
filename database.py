import os
import threading

DATABASE_URL = os.getenv("DATABASE_URL", "")

# Fix Railway's postgres:// → postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

USE_POSTGRES = bool(DATABASE_URL)

if USE_POSTGRES:
    import psycopg2
    from psycopg2 import pool as pg_pool
    PH = "%s"
    _pool = pg_pool.ThreadedConnectionPool(1, 20, DATABASE_URL)

    def _conn():
        return _pool.getconn()

    def _put(conn):
        _pool.putconn(conn)

    def _execute(query, params=(), fetch=None):
        conn = _conn()
        try:
            cur = conn.cursor()
            cur.execute(query, params)
            conn.commit()
            if fetch == "one":  return cur.fetchone()
            if fetch == "all":  return cur.fetchall()
        finally:
            cur.close()
            _put(conn)

    def init_db():
        _execute("""CREATE TABLE IF NOT EXISTS users
                    (telegram_id BIGINT PRIMARY KEY, email TEXT)""")
        _execute("""CREATE TABLE IF NOT EXISTS inbox
                    (id SERIAL PRIMARY KEY, email TEXT, sender TEXT,
                     subject TEXT, body TEXT,
                     time TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
        _execute("""CREATE TABLE IF NOT EXISTS email_history
                    (id SERIAL PRIMARY KEY, telegram_id BIGINT, email TEXT,
                     UNIQUE(telegram_id, email))""")

else:
    import sqlite3
    PH = "?"
    _local = threading.local()

    def _conn():
        if not hasattr(_local, "conn"):
            _local.conn = sqlite3.connect("tempmail.db", check_same_thread=False)
        return _local.conn

    def _execute(query, params=(), fetch=None):
        conn = _conn()
        cur = conn.cursor()
        cur.execute(query, params)
        conn.commit()
        if fetch == "one":  return cur.fetchone()
        if fetch == "all":  return cur.fetchall()

    def init_db():
        _execute(f"CREATE TABLE IF NOT EXISTS users (telegram_id INTEGER PRIMARY KEY, email TEXT)")
        _execute(f"CREATE TABLE IF NOT EXISTS inbox (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT, sender TEXT, subject TEXT, body TEXT, time DATETIME DEFAULT CURRENT_TIMESTAMP)")
        _execute(f"CREATE TABLE IF NOT EXISTS email_history (id INTEGER PRIMARY KEY AUTOINCREMENT, telegram_id INTEGER, email TEXT, UNIQUE(telegram_id, email))")


# ── Init on import ──────────────────────────────────────────────────────────
init_db()


# ── Public API ──────────────────────────────────────────────────────────────
def set_user_email(tg_id, email):
    _execute(f"INSERT INTO users (telegram_id, email) VALUES ({PH},{PH}) ON CONFLICT(telegram_id) DO UPDATE SET email=EXCLUDED.email" if USE_POSTGRES
             else f"REPLACE INTO users VALUES ({PH},{PH})", (tg_id, email))
    _execute(f"INSERT INTO email_history (telegram_id, email) VALUES ({PH},{PH}) ON CONFLICT DO NOTHING" if USE_POSTGRES
             else f"INSERT OR IGNORE INTO email_history (telegram_id, email) VALUES ({PH},{PH})", (tg_id, email))


def get_user_email(tg_id):
    r = _execute(f"SELECT email FROM users WHERE telegram_id={PH}", (tg_id,), fetch="one")
    return r[0] if r else None


def get_tg_id_by_email(email):
    r = _execute(f"SELECT telegram_id FROM users WHERE email={PH}", (email,), fetch="one")
    return r[0] if r else None


def save_email(email, sender, subject, body):
    _execute(f"INSERT INTO inbox (email,sender,subject,body) VALUES ({PH},{PH},{PH},{PH})",
             (email, sender, subject, body))


def get_inbox(email):
    return _execute(f"SELECT id,sender,subject,body,time FROM inbox WHERE email={PH} ORDER BY id DESC LIMIT 20",
                    (email,), fetch="all") or []


def get_email_by_id(mail_id):
    return _execute(f"SELECT sender,subject,body,time FROM inbox WHERE id={PH}", (mail_id,), fetch="one")


def get_user_all_emails(tg_id):
    rows = _execute(f"SELECT email FROM email_history WHERE telegram_id={PH} ORDER BY id DESC LIMIT 50",
                    (tg_id,), fetch="all") or []
    return [r[0] for r in rows]


def delete_email_address(tg_id, email):
    _execute(f"DELETE FROM email_history WHERE telegram_id={PH} AND email={PH}", (tg_id, email))
    _execute(f"DELETE FROM inbox WHERE email={PH}", (email,))
    _execute(f"DELETE FROM users WHERE telegram_id={PH} AND email={PH}", (tg_id, email))


def delete_single_mail(mail_id):
    _execute(f"DELETE FROM inbox WHERE id={PH}", (mail_id,))
