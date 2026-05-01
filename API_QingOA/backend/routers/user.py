from __future__ import annotations

from urllib.parse import urlparse

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.core.errors import AVATAR_URL_INVALID, USER_PROFILE_INVALID, ApiError
from backend.core.response import ok
from backend.db.database import get_db
from backend.db.models import User
from backend.dependencies import get_current_user
from backend.schemas.user import UserAvatarUpdateRequest, UserProfileUpdateRequest

router = APIRouter(prefix="/api/user", tags=["user"])


@router.get("/profile")
def profile(user: User = Depends(get_current_user)):
    return ok(_profile(user))


@router.put("/profile")
def update_profile(
    body: UserProfileUpdateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    phone = _clean_optional(body.phone)
    email = _clean_optional(body.email)
    office_location = _clean_optional(body.office_location)
    if phone is not None and len(phone) > 32:
        raise ApiError(USER_PROFILE_INVALID, "手机号长度不能超过 32 个字符")
    if email and ("@" not in email or len(email) > 120):
        raise ApiError(USER_PROFILE_INVALID, "邮箱格式不正确")
    if office_location is not None and len(office_location) > 80:
        raise ApiError(USER_PROFILE_INVALID, "办公地点长度不能超过 80 个字符")

    user.phone = phone
    user.email = email
    user.office_location = office_location
    db.commit()
    db.refresh(user)
    return ok(_profile(user), msg="个人资料已更新")


@router.post("/avatar")
def update_avatar(
    body: UserAvatarUpdateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    avatar_url = body.avatar_url.strip()
    if not _is_valid_avatar_url(avatar_url):
        raise ApiError(AVATAR_URL_INVALID, "头像地址必须是 http 或 https 图片 URL")
    user.avatar_url = avatar_url
    db.commit()
    db.refresh(user)
    return ok(_profile(user), msg="头像已更新")


def _profile(user: User) -> dict:
    return {
        "id": user.id,
        "user_id": user.id,
        "username": user.username,
        "name": user.name,
        "dept": user.dept,
        "role": user.role,
        "avatar_url": user.avatar_url or "",
        "phone": user.phone or "",
        "email": user.email or "",
        "office_location": user.office_location or "",
        "manager_id": user.manager_id,
        "is_hr": bool(user.is_hr),
        "has_punch_permission": bool(user.has_punch_permission),
    }


def _clean_optional(value: str | None) -> str:
    return value.strip() if value is not None else ""


def _is_valid_avatar_url(value: str) -> bool:
    if not value:
        return False
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return False
    path = parsed.path.lower()
    return path.endswith((".png", ".jpg", ".jpeg", ".webp", ".gif"))
