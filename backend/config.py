import os
from pathlib import Path
from zoneinfo import ZoneInfo

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.getenv("DATABASE_PATH", BASE_DIR / "transitnotice_tn.db"))

IST_TIMEZONE = ZoneInfo("Asia/Kolkata")
USER_AGENT = "TransitNoticeBot/1.0 (+https://github.com/transitnotice; compliance@transitnotice.local)"
REQUEST_TIMEOUT = 20  # 15s to 30s
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "transit_admin_secret_2026")
HOST = os.getenv("FLASK_HOST", "127.0.0.1")
PORT = int(os.getenv("FLASK_PORT", 5000))

