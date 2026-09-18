import os
import threading
from datetime import datetime, timedelta, timezone

import requests
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

=========================

تنظیمات

=========================

BOT_TOKEN = os.getenv(“BOT_TOKEN”)
PANEL_URL = os.getenv(“PANEL_URL”)
PANEL_TOKEN = os.getenv(“PANEL_TOKEN”)
PORT = int(os.getenv(“PORT”, “10000”))

web = Flask(name)

=========================

Health Check

=========================

@web.route(”/”)
def home():
return “Telegram VPN Bot is running!”

def run_web():
web.run(host=“0.0.0.0”, port=PORT)

=========================

ساخت Client در پنل

=========================

def create_client(email, telegram_id):

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
headers = {
    "Authorization": f"Bearer {PANEL_TOKEN}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}
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

=========================

Telegram /start

=========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

await update.message.reply_text(
    "سلام 👋\n\n"
    "🤖 ربات فروش کانفیگ آماده است.\n\n"
    "برای تست ساخت کانفیگ:\n"
    "/buy"
)

=========================

Telegram /buy

=========================

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):

user = update.effective_user
try:
    email = f"tg-{user.id}"
    result = create_client(
        email=email,
        telegram_id=user.id
    )
    print("CREATE CLIENT RESULT:", result)
    if result.get("success"):
        await update.message.reply_text(
            "✅ کانفیگ با موفقیت ساخته شد!\n\n"
            "📦 حجم: 50GB\n"
            "⏳ اعتبار: 7 روز"
        )
    else:
        await update.message.reply_text(
            "❌ ساخت کانفیگ ناموفق بود.\n\n"
            f"پیام پنل: {result.get('msg', 'نامشخص')}"
        )
except Exception as e:
    import traceback
    print("ERROR:", repr(e))
    traceback.print_exc()
    await update.message.reply_text(
        "❌ اتصال به پنل با خطا مواجه شد."
    )

=========================

Main

=========================

def main():

threading.Thread(
    target=run_web,
    daemon=True
).start()
app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(
    CommandHandler("start", start)
)
app.add_handler(
    CommandHandler("buy", buy)
)
print("Bot is running...")
app.run_polling()

=========================

Start

=========================

if name == “main”:
main()
