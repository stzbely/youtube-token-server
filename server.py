import os
import sqlite3
import requests
from datetime import datetime
from flask import Flask, request, jsonify

from database import init_db, get_token, bind_hwid

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "licenses.db")

app = Flask(__name__)
init_db()

print("DB PATH:", DB_PATH)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
ADMIN_KEY = os.getenv("ADMIN_KEY", "")


def notify_telegram(text):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return

    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": text,
                "parse_mode": "HTML"
            },
            timeout=8
        )
    except Exception:
        pass


@app.route("/")
def home():
    return jsonify({
        "ok": True,
        "message": "Token server works",
        "db_path": DB_PATH
    })


@app.route("/check-token", methods=["POST"])
def check_token():
    data = request.json or {}

    token = data.get("token", "").strip()
    hwid = data.get("hwid", "").strip()
    app_version = data.get("version", "").strip()

    if not token:
        return jsonify({"ok": False, "reason": "Токен не указан"})

    row = get_token(token)

    if not row:
        notify_telegram(
            f"❌ Неизвестный токен\n"
            f"Token: <code>{token}</code>\n"
            f"HWID: <code>{hwid}</code>"
        )
        return jsonify({"ok": False, "reason": "Токен не найден"})

    if not row["active"]:
        return jsonify({"ok": False, "reason": "Токен отключён"})

    expires = datetime.strptime(row["expires"], "%Y-%m-%d")

    if datetime.now() > expires:
        return jsonify({"ok": False, "reason": "Подписка истекла"})

    saved_hwid = row.get("hwid") or ""

    if hwid:
        if not saved_hwid:
            bind_hwid(token, hwid)
            notify_telegram(
                f"✅ Новая активация\n"
                f"User: {row['user']}\n"
                f"Token: <code>{token}</code>\n"
                f"HWID: <code>{hwid}</code>\n"
                f"До: {row['expires']}\n"
                f"Версия: {app_version}"
            )

        elif saved_hwid != hwid:
            return jsonify({
                "ok": False,
                "reason": "Токен уже активирован на другом устройстве"
            })

    return jsonify({
        "ok": True,
        "user": row["user"],
        "expires": row["expires"],
        "hwid": hwid or saved_hwid,
        "server_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })


@app.route("/add-token", methods=["POST"])
def add_token():
    data = request.json or {}

    admin_key = data.get("admin_key", "").strip()
    token = data.get("token", "").strip()
    user = data.get("user", "").strip()
    expires = data.get("expires", "").strip()

    if not ADMIN_KEY:
        return jsonify({"ok": False, "reason": "ADMIN_KEY не настроен"}), 500

    if admin_key != ADMIN_KEY:
        return jsonify({"ok": False, "reason": "Нет доступа"}), 403

    if not token or not user or not expires:
        return jsonify({"ok": False, "reason": "Не все поля заполнены"}), 400

    try:
        datetime.strptime(expires, "%Y-%m-%d")
    except ValueError:
        return jsonify({"ok": False, "reason": "Дата должна быть YYYY-MM-DD"}), 400

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO tokens (
                token,
                user,
                active,
                expires,
                hwid,
                created_at
            )
            VALUES (?, ?, 1, ?, '', ?)
        """, (
            token,
            user,
            expires,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

        conn.commit()
        conn.close()

    except sqlite3.IntegrityError:
        return jsonify({"ok": False, "reason": "Такой токен уже существует"}), 409

    except Exception as e:
        return jsonify({"ok": False, "reason": str(e)}), 500

    notify_telegram(
        f"🆕 Создан новый токен\n"
        f"User: {user}\n"
        f"Token: <code>{token}</code>\n"
        f"До: {expires}"
    )

    return jsonify({
        "ok": True,
        "token": token,
        "user": user,
        "expires": expires
    })


@app.route("/version", methods=["GET"])
def version():
    return jsonify({
        "ok": True,
        "latest_version": "1.0.0",
        "download_url": "",
        "notes": "Первая коммерческая версия"
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)