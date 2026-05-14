from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.core.response import ok
from backend.db.database import get_db
from backend.db.models import User
from backend.dependencies import get_current_user
from backend.schemas.leave import LeaveCreateRequest
from backend.services import leave_service

router = APIRouter(prefix="/api/leave", tags=["leave"])


@router.post("/requests")
def create_leave_request(
    body: LeaveCreateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ok(leave_service.create_leave_request(db, user, body), msg="请假申请已提交")


@router.post("/requests/{leave_id}/cancel")
def cancel_leave_request(
    leave_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ok(leave_service.cancel_leave_request(db, user, leave_id), msg="请假申请已取消")
