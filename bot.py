import os
import threading
from datetime import datetime, timedelta, timezone

import requests
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
PANEL_URL = os.getenv("PANEL_URL")
PANEL_TOKEN = os.getenv("PANEL_TOKEN")
PORT = int(os.getenv("PORT", "10000"))

web = Flask(__name__)


@web.route("/")
def home():
    return "Telegram VPN Bot is running!"


def run_web():
    web.run(host="0.0.0.0", port=PORT)


def create_client(user_id):
    expiry = datetime.now(timezone.utc) + timedelta(days=7)

    payload = {
        "client": {
            "email": f"tg-{user_id}",
            "totalGB": 50 * 1024 * 1024 * 1024,
            "expiryTime": int(expiry.timestamp() * 1000),
            "tgId": user_id,
            "limitIp": 0,
            "enable": True
        },
        "inboundIds": [1]
    }

    headers = {
        "Authorization": f"Bearer {PANEL_TOKEN}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    url = PANEL_URL.rstrip("/") + "/panel/api/clients/add"

    response = requests.post(
        url,
        json=payload,
        headers=headers,
        timeout=20
    )

    print("PANEL STATUS:", response.status_code)
    print("PANEL RESPONSE:", response.text)

    response.raise_for_status()

    return response.json()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام 👋\n\n"
        "🤖 ربات فروش کانفیگ آماده است.\n\n"
        "برای تست ساخت کانفیگ:\n"
        "/buy"
    )


async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    try:
        result = create_client(user_id)

        if result.get("success"):
            await update.message.reply_text(
                "✅ کانفیگ با موفقیت ساخته شد!\n\n"
                "📦 حجم: 50GB\n"
                "⏳ اعتبار: 7 روز"
            )
        else:
            await update.message.reply_text(
                f"❌ ساخت کانفیگ ناموفق بود.\n{result.get('msg', '')}"
            )

    except Exception as e:
        print("ERROR:", repr(e))
        await update.message.reply_text(
            "❌ اتصال به پنل با خطا مواجه شد."
        )


def main():
    threading.Thread(target=run_web, daemon=True).start()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("buy", buy))

    print("Bot is running...")

    app.run_polling()


if __name__ == "__main__":
    main()
