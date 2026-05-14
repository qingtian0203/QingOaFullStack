from __future__ import annotations

import os
from pathlib import Path
from zoneinfo import ZoneInfo


PROJECT_ROOT = Path(__file__).resolve().parents[2]
FULLSTACK_ROOT = PROJECT_ROOT.parent
DATA_DIR = PROJECT_ROOT / "data"
STATIC_DIR = PROJECT_ROOT / "static"
UPLOAD_DIR = STATIC_DIR / "uploads"
WAP_DIST_DIR = FULLSTACK_ROOT / "WAP_QingOA" / "dist"
DATABASE_URL = os.getenv("QINGOA_DATABASE_URL", f"sqlite:///{DATA_DIR / 'qing_oa_v1.db'}")

APP_NAME = "Qing OA FullStack V1"
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 8010
SERVER_TIMEZONE = ZoneInfo("Asia/Shanghai")
TOKEN_EXPIRE_DAYS = 7
MAX_UPLOAD_SIZE_BYTES = 5 * 1024 * 1024

# v1.6B 固定班次规则。后续如需多班次，再迁移到 shift_schedules 表。
SHIFT_START = "09:00"
SHIFT_END = "18:00"
LATE_GRACE = 10
EARLY_GRACE = 10

# v1.7 请假流程：超过 3 天进入 HR 二审。
LEAVE_HR_REVIEW_THRESHOLD_DAYS = 3
