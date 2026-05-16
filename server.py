from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

TOKENS = {
    "STZBELY-2026-PRO": {
        "active": True,
        "expires": "2026-12-31",
        "user": "client_1"
    },

    "IVAN-1MONTH": {
        "active": True,
        "expires": "2026-06-30",
        "user": "ivan"
    }
}


@app.route("/")
def home():
    return "Token server works"


@app.route("/check-token", methods=["POST"])
def check_token():
    data = request.json or {}
    token = data.get("token", "").strip()

    if token not in TOKENS:
        return jsonify({
            "ok": False,
            "reason": "Токен не найден"
        })

    token_data = TOKENS[token]

    if not token_data["active"]:
        return jsonify({
            "ok": False,
            "reason": "Токен отключен"
        })

    expires = datetime.strptime(token_data["expires"], "%Y-%m-%d")

    if datetime.now() > expires:
        return jsonify({
            "ok": False,
            "reason": "Подписка истекла"
        })

    return jsonify({
        "ok": True,
        "user": token_data["user"],
        "expires": token_data["expires"]
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)