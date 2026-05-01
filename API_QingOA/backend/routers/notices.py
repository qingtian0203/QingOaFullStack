from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.core import time_provider
from backend.core.errors import ApiError, RESOURCE_NOT_FOUND
from backend.core.response import ok
from backend.db.database import get_db
from backend.db.models import Notice, NoticeRead, User
from backend.dependencies import get_current_user

router = APIRouter(prefix="/api/notices", tags=["notices"])


@router.get("/{notice_id}")
def detail(
    notice_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    notice = db.get(Notice, notice_id)
    if notice is None:
        raise ApiError(RESOURCE_NOT_FOUND, "通知不存在或无权限访问")
    return ok(
        {
            "id": notice.id,
            "title": notice.title,
            "content": notice.content,
            "created_at": time_provider.fmt(notice.created_at),
            "is_read": _is_read(db, user.id, notice.id),
        }
    )


@router.post("/{notice_id}/read")
def mark_read(
    notice_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    notice = db.get(Notice, notice_id)
    if notice is None:
        raise ApiError(RESOURCE_NOT_FOUND, "通知不存在或无权限访问")
    row = db.scalar(
        select(NoticeRead)
        .where(NoticeRead.user_id == user.id)
        .where(NoticeRead.notice_id == notice_id)
    )
    if row is None:
        db.add(NoticeRead(user_id=user.id, notice_id=notice_id))
        db.commit()
    return ok(None, msg="通知已读")


def _is_read(db: Session, user_id: int, notice_id: int) -> bool:
    row = db.scalar(
        select(NoticeRead.id)
        .where(NoticeRead.user_id == user_id)
        .where(NoticeRead.notice_id == notice_id)
    )
    return row is not None
