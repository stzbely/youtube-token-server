import os
import requests
from datetime import datetime
from flask import Flask, request, jsonify

from database import init_db, get_token, bind_hwid

app = Flask(__name__)
init_db()

TELEGRAM_BOT_TOKEN = os.getenv("8670862501:AAGqMpSIlhm_OF8eIgxtetFxphPXhYpnIrk", "")
TELEGRAM_CHAT_ID = os.getenv("1092718145", "")


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
        "message": "Token server works"
    })


@app.route("/check-token", methods=["POST"])
def check_token():
    data = request.json or {}

    token = data.get("token", "").strip()
    hwid = data.get("hwid", "").strip()
    app_version = data.get("version", "").strip()

    if not token:
        return jsonify({
            "ok": False,
            "reason": "Токен не указан"
        })

    row = get_token(token)

    if not row:
        notify_telegram(f"❌ Неизвестный токен\nToken: <code>{token}</code>\nHWID: <code>{hwid}</code>")
        return jsonify({
            "ok": False,
            "reason": "Токен не найден"
        })

    if not row["active"]:
        notify_telegram(f"⛔ Отключённый токен пытался войти\nUser: {row['user']}\nToken: <code>{token}</code>")
        return jsonify({
            "ok": False,
            "reason": "Токен отключён"
        })

    expires = datetime.strptime(row["expires"], "%Y-%m-%d")

    if datetime.now() > expires:
        return jsonify({
            "ok": False,
            "reason": "Подписка истекла"
        })

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
            notify_telegram(
                f"🚫 Попытка входа с другого ПК\n"
                f"User: {row['user']}\n"
                f"Token: <code>{token}</code>\n"
                f"Saved HWID: <code>{saved_hwid}</code>\n"
                f"New HWID: <code>{hwid}</code>"
            )

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
