
import os
import uuid
import requests
from datetime import datetime, timedelta, timezone

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes


# =========================
# تنظیمات از Environment
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")
PANEL_URL = os.getenv("PANEL_URL")       # مثال: http://1.2.3.4:2053
PANEL_USER = os.getenv("PANEL_USER")
PANEL_PASS = os.getenv("PANEL_PASS")

session = requests.Session()


# =========================
# ورود به پنل
# =========================

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
        raise Exception("Login to panel failed")

    return True


# =========================
# ساخت کانفیگ
# =========================

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


# =========================
# Telegram
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    await update.message.reply_text(
        f"سلام {user.first_name} 👋\n\n"
        "🤖 ربات فروش کانفیگ آماده است.\n\n"
        "برای تست ساخت کانفیگ، دستور زیر را بزن:\n"
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

        if result.get("success"):
            await update.message.reply_text(
                "✅ کانفیگ با موفقیت ساخته شد!\n\n"
                f"👤 شناسه: {user.id}\n"
                "📦 حجم: 50GB\n"
                "⏳ اعتبار: 7 روز"
            )
        else:
            await update.message.reply_text(
                "❌ ساخت کانفیگ ناموفق بود."
            )

    except Exception as e:

        print("ERROR:", e)

        await update.message.reply_text(
            "❌ خطایی هنگام اتصال به پنل رخ داد."
        )


# =========================
# اجرای ربات
# =========================

def main():

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("buy", buy))

    print("Bot is running...")

    app.run_polling()


if __name__ == "__main__":
    main()
