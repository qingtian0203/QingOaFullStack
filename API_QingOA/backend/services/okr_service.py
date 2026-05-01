from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend.core import time_provider
from backend.core.errors import ApiError, BAD_REQUEST, RESOURCE_NOT_FOUND
from backend.db.models import KeyResult, Okr, User
from backend.schemas.okr import KrProgressUpdateRequest, OkrCreateRequest


def list_okrs(db: Session, user: User, period: str | None = None) -> dict:
    query = (
        select(Okr)
        .options(selectinload(Okr.key_results))
        .where(Okr.user_id == user.id)
        .where(Okr.status != "cancelled")
        .order_by(Okr.updated_at.desc(), Okr.id.desc())
    )
    if period:
        query = query.where(Okr.period == period)
    rows = db.scalars(query).all()
    return {"list": [_okr_list_item(row) for row in rows]}


def get_okr(db: Session, user: User, okr_id: int) -> dict:
    okr = _own_okr(db, user, okr_id)
    return _okr_detail(okr)


def create_okr(db: Session, user: User, body: OkrCreateRequest) -> dict:
    key_results = [
        KeyResult(
            title=_required(kr.title, "KR 标题不能为空"),
            target_value=kr.target_value,
            current_value=kr.current_value,
            unit=_required(kr.unit, "KR 单位不能为空"),
        )
        for kr in body.key_results
    ]
    if not key_results:
        raise ApiError(BAD_REQUEST, "至少需要 1 个 KR")

    current = time_provider.now()
    okr = Okr(
        user_id=user.id,
        title=_required(body.title, "OKR 标题不能为空"),
        description=(body.description or "").strip() or None,
        period=_required(body.period, "OKR 周期不能为空"),
        status="active",
        created_at=current,
        updated_at=current,
    )
    okr.key_results = key_results
    db.add(okr)
    db.commit()
    db.refresh(okr)
    return {"id": okr.id}


def update_key_result_progress(
    db: Session,
    user: User,
    okr_id: int,
    kr_id: int,
    body: KrProgressUpdateRequest,
) -> dict:
    okr = _own_okr(db, user, okr_id)
    kr = next((item for item in okr.key_results if item.id == kr_id), None)
    if kr is None:
        raise ApiError(RESOURCE_NOT_FOUND, "KR 不存在或无权限访问")

    kr.current_value = body.current_value
    kr.updated_at = time_provider.now()
    okr.updated_at = kr.updated_at
    db.commit()
    db.refresh(okr)
    return {
        "kr_progress": _kr_progress(kr),
        "okr_progress": _okr_progress(okr),
    }


def delete_okr(db: Session, user: User, okr_id: int) -> None:
    okr = _own_okr(db, user, okr_id)
    okr.status = "cancelled"
    okr.updated_at = time_provider.now()
    db.commit()


def _own_okr(db: Session, user: User, okr_id: int) -> Okr:
    okr = db.scalar(
        select(Okr)
        .options(selectinload(Okr.key_results))
        .where(Okr.id == okr_id)
        .where(Okr.user_id == user.id)
        .where(Okr.status != "cancelled")
    )
    if okr is None:
        raise ApiError(RESOURCE_NOT_FOUND, "OKR 不存在或无权限访问")
    return okr


def _required(value: str | None, message: str) -> str:
    text = (value or "").strip()
    if not text:
        raise ApiError(BAD_REQUEST, message)
    return text


def _okr_list_item(okr: Okr) -> dict:
    return {
        "id": okr.id,
        "title": okr.title,
        "description": okr.description,
        "period": okr.period,
        "status": okr.status,
        "progress": _okr_progress(okr),
        "kr_count": len(okr.key_results),
        "created_at": _fmt_dt(okr.created_at),
        "updated_at": _fmt_dt(okr.updated_at),
    }


def _okr_detail(okr: Okr) -> dict:
    return {
        **_okr_list_item(okr),
        "key_results": [_kr_item(kr) for kr in okr.key_results],
    }


def _kr_item(kr: KeyResult) -> dict:
    return {
        "id": kr.id,
        "title": kr.title,
        "target_value": kr.target_value,
        "current_value": kr.current_value,
        "unit": kr.unit,
        "progress": _kr_progress(kr),
    }


def _okr_progress(okr: Okr) -> int:
    if not okr.key_results:
        return 0
    return round(sum(_kr_progress(kr) for kr in okr.key_results) / len(okr.key_results))


def _kr_progress(kr: KeyResult) -> int:
    if kr.target_value <= 0:
        return 0
    return round(min(kr.current_value / kr.target_value, 1.0) * 100)


def _fmt_dt(value: datetime | None) -> str | None:
    return time_provider.fmt(value) if value else None
