import os
import threading
from datetime import datetime, timedelta, timezone

import requests
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes


BOT_TOKEN = os.getenv("BOT_TOKEN")
PANEL_URL = os.getenv("PANEL_URL")
PANEL_USER = os.getenv("PANEL_USER")
PANEL_PASS = os.getenv("PANEL_PASS")

PORT = int(os.getenv("PORT", "10000"))

session = requests.Session()

web = Flask(__name__)


@web.route("/")
def home():
    return "Telegram VPN Bot is running!"


def run_web():
    web.run(host="0.0.0.0", port=PORT)


def panel_login():

    url = PANEL_URL.rstrip("/") + "/login"

    data = {
        "username": PANEL_USER,
        "password": PANEL_PASS,
        "twoFactorCode": ""
    }

    response = session.post(url, json=data, timeout=15)
    response.raise_for_status()

    result = response.json()

    if not result.get("success"):
        raise Exception(f"Panel login failed: {result}")

    return True


def create_client(email, telegram_id):

    panel_login()

    expiry = datetime.now(timezone.utc) + timedelta(days=7)

    payload = {
        "client": {
            "email": email,
            "totalGB": 50 * 1024 * 1024 * 1024,
            "expiryTime": int(expiry.timestamp() * 1000),
            "tgId": telegram_id,
            "limitIp": 0,
            "enable": True
        },
        "inboundIds": [1]
    }

    url = PANEL_URL.rstrip("/") + "/panel/api/clients/add"

    response = session.post(url, json=payload, timeout=15)
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

    user = update.effective_user

    try:

        email = f"tg-{user.id}"

        result = create_client(
            email=email,
            telegram_id=user.id
        )

        print("PANEL RESPONSE:", result)

        if result.get("success"):

            await update.message.reply_text(
                "✅ کانفیگ با موفقیت ساخته شد!\n\n"
                "📦 حجم: 50GB\n"
                "⏳ اعتبار: 7 روز"
            )

        else:

            await update.message.reply_text(
                "❌ ساخت کانفیگ ناموفق بود."
            )

    except Exception as e:

        import traceback

        print("ERROR:", repr(e))
        traceback.print_exc()

        await update.message.reply_text(
            "❌ اتصال به پنل با خطا مواجه شد."
        )


def main():

    threading.Thread(
        target=run_web,
        daemon=True
    ).start()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("buy", buy))

    print("Bot is running...")

    app.run_polling()


if __name__ == "__main__":
    main()
