from __future__ import annotations

import os
from pathlib import Path
from zoneinfo import ZoneInfo


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
DATABASE_URL = os.getenv("QINGOA_DATABASE_URL", f"sqlite:///{DATA_DIR / 'qing_oa_v1.db'}")

APP_NAME = "Qing OA FullStack V1"
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 8010
SERVER_TIMEZONE = ZoneInfo("Asia/Shanghai")
TOKEN_EXPIRE_DAYS = 7
