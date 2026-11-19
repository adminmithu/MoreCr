import sys
import io
import os

# Fix Windows console UTF-8 output encoding for emojis & Bengali
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

import logging
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)

from config import (
    BOT_TOKEN,
    ADMIN_IDS,
    ENABLE_WEB_DASHBOARD,
    WEB_DASHBOARD_PORT,
    DEFAULT_EMAIL_PREFIX
)
from database.db import Database
from bot.handlers import (
    start_handler,
    text_message_handler,
    reply_command
)
from web.dashboard import start_web_dashboard

# Logging configuration
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def dummy_callback(update, context):
    if update.callback_query:
        await update.callback_query.answer()

def main():
    print("""
============================================================
       ⚡ MoreLogin Account Creator Telegram Bot ⚡
============================================================
    """)

    # Check Bot Token
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        print("❌ [ERROR]: Telegram Bot Token পাওয়া যায়নি!")
        print("👉 অনুগ্রহ করে '.env' ফাইলটি খুলুন এবং BOT_TOKEN= আপনার বটের টোকেন দিন।")
        return

    # Initialize Database
    db = Database()
    print("✅ Database initialized successfully.")

    # Start Web Dashboard if enabled
    if ENABLE_WEB_DASHBOARD:
        start_web_dashboard(WEB_DASHBOARD_PORT)

    # Build Telegram Bot Application
    application = Application.builder().token(BOT_TOKEN).build()

    # Handlers (All ReplyKeyboard based)
    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("reply", reply_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message_handler))
    application.add_handler(CallbackQueryHandler(dummy_callback))

    admin_list = ", ".join(str(aid) for aid in ADMIN_IDS) if ADMIN_IDS else "None set"
    print(f"🤖 Bot Polling Started...")
    print(f"👑 Admin ID          : {admin_list}")
    print(f"📧 Default Mailbox   : {DEFAULT_EMAIL_PREFIX}@muellfach.de")
    if ENABLE_WEB_DASHBOARD:
        print(f"🌐 Realtime Dashboard: http://localhost:{WEB_DASHBOARD_PORT}/")
    print("\n🚀 বটটি সফলভাবে চালু হয়েছে! টেলিগ্রামের /start লিখে টেস্ট করুন...\n")

    # Run bot polling
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
