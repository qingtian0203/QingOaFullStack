from __future__ import annotations

from datetime import datetime

from .config import SERVER_TIMEZONE

_frozen_time: datetime | None = None


def now() -> datetime:
    if _frozen_time is not None:
        return _frozen_time
    return datetime.now(SERVER_TIMEZONE).replace(tzinfo=None)


def freeze(value: datetime) -> datetime:
    global _frozen_time
    _frozen_time = value.replace(tzinfo=None)
    return _frozen_time


def unfreeze() -> None:
    global _frozen_time
    _frozen_time = None


def frozen_time() -> datetime | None:
    return _frozen_time


def fmt(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.strftime("%Y-%m-%d %H:%M:%S")

