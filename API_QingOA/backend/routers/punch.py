from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.core.response import ok
from backend.db.database import get_db
from backend.db.models import User
from backend.dependencies import get_current_user
from backend.schemas.punch import ClockInRequest, ClockRequest, PunchAppealCreateRequest, PunchAppealReviewRequest
from backend.services import punch_service

router = APIRouter(prefix="/api/punch", tags=["punch"])


@router.get("/today-status")
def today_status(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return ok(punch_service.today_status(db, user))


@router.post("/clock-in")
def clock_in(
    body: ClockInRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = punch_service.clock_in(db, user, body.lat, body.lng, body.device_id)
    return ok(result, msg="打卡已更新" if result.get("updated") else "打卡成功")


@router.post("/clock")
def clock(
    body: ClockRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = punch_service.clock(db, user, body.lat, body.lng, body.device_id, body.punch_type)
    if body.punch_type == "clock_in":
        msg = "上班打卡成功"
    elif result.get("updated"):
        msg = "下班打卡时间已更新"
    else:
        msg = "下班打卡成功"
    return ok(result, msg=msg)


@router.get("/records")
def records(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
):
    return ok(punch_service.records(db, user, page, size))


@router.get("/records/{record_id}")
def record_detail(
    record_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ok(punch_service.record_detail(db, user, record_id))


@router.post("/appeal")
def create_appeal(
    body: PunchAppealCreateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ok(
        punch_service.create_appeal(
            db,
            user,
            body.punch_date,
            body.punch_type,
            body.reason,
            body.expect_time,
        ),
        msg="补卡申诉已提交",
    )


@router.get("/appeals")
def my_appeals(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return ok(punch_service.my_appeals(db, user))


@router.get("/appeals/pending-review")
def pending_review_appeals(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return ok(punch_service.pending_review_appeals(db, user))


@router.post("/appeals/{appeal_id}/review")
def review_appeal(
    appeal_id: int,
    body: PunchAppealReviewRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ok(
        punch_service.review_appeal(db, user, appeal_id, body.action, body.note),
        msg="审批已处理",
    )


@router.get("/monthly-summary")
def monthly_summary(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    month: str | None = Query(None, pattern=r"^\d{4}-\d{2}$"),
):
    return ok(punch_service.monthly_summary(db, user, month))
