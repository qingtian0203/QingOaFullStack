from __future__ import annotations

from fastapi import Depends, Header
from sqlalchemy.orm import Session

from backend.core.errors import ApiError, INVALID_TOKEN
from backend.db.database import get_db
from backend.db.models import User
from backend.services.auth_service import require_valid_user


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    return require_valid_user(db, bearer_from_header(authorization))


def bearer_from_header(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise ApiError(INVALID_TOKEN, "Token 无效或已过期")
    token = authorization[7:].strip()
    if not token:
        raise ApiError(INVALID_TOKEN, "Token 无效或已过期")
    return token
