from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.core.response import ok
from backend.db.database import get_db
from backend.db.models import User
from backend.dependencies import get_current_user
from backend.schemas.okr import KrProgressUpdateRequest, OkrCreateRequest
from backend.services import okr_service

router = APIRouter(prefix="/api/okr", tags=["okr"])


@router.get("/list")
def okr_list(
    period: str | None = Query(default=None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ok(okr_service.list_okrs(db, user, period))


@router.get("/{okr_id}")
def okr_detail(
    okr_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ok(okr_service.get_okr(db, user, okr_id))


@router.post("/create")
def okr_create(
    body: OkrCreateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ok(okr_service.create_okr(db, user, body))


@router.put("/{okr_id}/key-results/{kr_id}")
def update_key_result_progress(
    okr_id: int,
    kr_id: int,
    body: KrProgressUpdateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ok(okr_service.update_key_result_progress(db, user, okr_id, kr_id, body))


@router.delete("/{okr_id}")
def okr_delete(
    okr_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    okr_service.delete_okr(db, user, okr_id)
    return ok()
