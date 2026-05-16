import sqlite3
import secrets
from datetime import datetime, timedelta

DB_PATH = "licenses.db"


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tokens (
            token TEXT PRIMARY KEY,
            user TEXT NOT NULL,
            active INTEGER NOT NULL DEFAULT 1,
            expires TEXT NOT NULL,
            hwid TEXT DEFAULT '',
            max_devices INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def generate_token(prefix="STZBELY"):
    part1 = secrets.token_hex(3).upper()
    part2 = secrets.token_hex(3).upper()
    part3 = secrets.token_hex(3).upper()
    return f"{prefix}-{part1}-{part2}-{part3}"


def create_token(user, days=30, max_devices=1, token=None):
    init_db()

    token = token or generate_token()
    expires = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = db()
    conn.execute("""
        INSERT INTO tokens (token, user, active, expires, hwid, max_devices, created_at)
        VALUES (?, ?, 1, ?, '', ?, ?)
    """, (token, user, expires, max_devices, created_at))
    conn.commit()
    conn.close()

    return token, expires


def get_token(token):
    init_db()
    conn = db()
    row = conn.execute("SELECT * FROM tokens WHERE token=?", (token,)).fetchone()
    conn.close()
    return dict(row) if row else None


def bind_hwid(token, hwid):
    conn = db()
    conn.execute("UPDATE tokens SET hwid=? WHERE token=?", (hwid, token))
    conn.commit()
    conn.close()


def set_active(token, active):
    conn = db()
    conn.execute("UPDATE tokens SET active=? WHERE token=?", (1 if active else 0, token))
    conn.commit()
    conn.close()


def extend_token(token, days):
    row = get_token(token)
    if not row:
        return False

    current_expires = datetime.strptime(row["expires"], "%Y-%m-%d")
    base = max(current_expires, datetime.now())
    new_expires = (base + timedelta(days=days)).strftime("%Y-%m-%d")

    conn = db()
    conn.execute("UPDATE tokens SET expires=? WHERE token=?", (new_expires, token))
    conn.commit()
    conn.close()
    return new_expires


def list_tokens():
    init_db()
    conn = db()
    rows = conn.execute("SELECT * FROM tokens ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]