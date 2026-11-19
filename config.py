import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# Telegram Bot Token
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

# Admin IDs
raw_admin_ids = os.getenv("ADMIN_IDS", "0")
ADMIN_IDS = set()
for aid in raw_admin_ids.split(","):
    aid = aid.strip()
    if aid.isdigit():
        ADMIN_IDS.add(int(aid))

# Email Defaults
DEFAULT_EMAIL_PREFIX = os.getenv("DEFAULT_EMAIL_PREFIX", "priyaahmed210208").strip()
MUELLFACH_DOMAIN = "muellfach.de"

# Password Settings
DEFAULT_PASSWORD = os.getenv("DEFAULT_PASSWORD", "MoreLogin@2026!").strip()

# Realtime Admin Notifications
REALTIME_ADMIN_PUSH = os.getenv("REALTIME_ADMIN_PUSH", "true").lower() in ("true", "1", "yes")

# Web Dashboard (Reads PORT from Render.com or fallback to 8080)
ENABLE_WEB_DASHBOARD = os.getenv("ENABLE_WEB_DASHBOARD", "true").lower() in ("true", "1", "yes")
WEB_DASHBOARD_PORT = int(os.getenv("PORT", os.getenv("WEB_DASHBOARD_PORT", "8080")))

# Database path (Supports Render persistent disk /var/data or local ./data)
DATA_DIR = Path(os.getenv("DATA_DIR", str(BASE_DIR / "data")))
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "morelogin.db"

# MoreLogin Crypto & API constants
MORELOGIN_CODEC_BASE = "3ALjw82GjMN3j/f5gpKp8g=="
MORELOGIN_REGISTER_URL = "https://cb-gateway.morelogin.com/app/user/register/home"
MORELOGIN_ACTIVATION_BASE = "https://cb-gateway.morelogin.com/app/member/activate"
MUELLFACH_API_URL = "https://www.muellfach.de/api.php"
MUELLFACH_SYNC_URL = "https://www.muellfach.de/sync.php"

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS
