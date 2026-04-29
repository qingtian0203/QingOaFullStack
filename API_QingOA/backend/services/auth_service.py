from __future__ import annotations

from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.core import time_provider
from backend.core.errors import ApiError, INVALID_CREDENTIALS, INVALID_TOKEN
from backend.core.security import new_token, verify_password
from backend.db.models import User


def public_user(user: User, token: str | None = None) -> dict:
    data = {
        "user_id": user.id,
        "username": user.username,
        "name": user.name,
        "dept": user.dept,
        "role": user.role,
        "has_punch_permission": bool(user.has_punch_permission),
    }
    if token is not None:
        data["token"] = token
    return data


def login(db: Session, username: str, password: str) -> dict:
    user = db.scalar(select(User).where(User.username == username))
    if user is None or not verify_password(password, user.password):
        raise ApiError(INVALID_CREDENTIALS, "账号或密码错误")

    token = new_token()
    user.token = token
    user.token_expires_at = time_provider.now() + timedelta(days=7)
    db.commit()
    db.refresh(user)
    return public_user(user, token=token)


def logout(db: Session, user: User) -> None:
    user.token = None
    user.token_expires_at = None
    db.commit()


def get_user_by_token(db: Session, token: str | None) -> User | None:
    if not token:
        return None
    return db.scalar(select(User).where(User.token == token))


def require_valid_user(db: Session, token: str | None) -> User:
    user = get_user_by_token(db, token)
    if user is None:
        raise ApiError(INVALID_TOKEN, "Token 无效或已过期")
    if user.token_expires_at is None or user.token_expires_at < time_provider.now():
        raise ApiError(INVALID_TOKEN, "Token 已过期，请重新登录")
    return user

