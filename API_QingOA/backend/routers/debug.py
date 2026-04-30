from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.core import time_provider
from backend.core.response import ok
from backend.db.database import create_tables, get_db
from backend.db.models import PunchRecord, User
from backend.db.seed import reset_database
from backend.schemas.debug import FreezeTimeRequest, ResetTodayPunchRequest, ScenarioRequest
from backend.services import debug_service, punch_service

router = APIRouter(prefix="/debug", tags=["debug"])


@router.post("/reset-data")
def reset_data(db: Session = Depends(get_db)):
    create_tables()
    reset_database(db)
    debug_service.reset_runtime_state()
    return ok(None, msg="数据已重置")


@router.post("/inject-scenario")
def inject_scenario(body: ScenarioRequest):
    scenario = debug_service.add_scenario(
        method=body.method,
        path=body.path,
        response=body.response,
        times=body.times,
        user_id=body.user_id,
        delay_ms=body.delay_ms,
        http_status=body.http_status,
    )
    return ok({"scenario_id": scenario.id}, msg="场景已注入")


@router.get("/scenarios")
def scenarios():
    return ok({"scenarios": debug_service.list_scenarios()})


@router.delete("/scenarios")
def clear_scenarios():
    debug_service.clear_scenarios()
    return ok(None, msg="已清除所有场景")


@router.delete("/scenarios/{scenario_id}")
def delete_scenario(scenario_id: str):
    debug_service.delete_scenario(scenario_id)
    return ok(None, msg="已清除")


@router.get("/state")
def state(db: Session = Depends(get_db)):
    active_users = db.scalars(select(User).where(User.token.is_not(None))).all()
    start, end = _today_range()
    today_records = db.scalars(
        select(PunchRecord)
        .where(PunchRecord.punch_date == time_provider.now().date().isoformat())
        .order_by(PunchRecord.punch_time.desc())
    ).all()
    return ok(
        {
            "active_users": [
                {
                    "user_id": user.id,
                    "username": user.username,
                    "token_expires_at": time_provider.fmt(user.token_expires_at),
                }
                for user in active_users
            ],
            "today_punch_records": [
                {
                    "user_id": row.user_id,
                    "punch_type": row.punch_type,
                    "punch_date": row.punch_date,
                    "punch_time": time_provider.fmt(row.punch_time),
                    "distance": row.distance,
                }
                for row in today_records
            ],
            "active_scenarios": debug_service.list_scenarios(),
            "frozen_time": time_provider.fmt(time_provider.frozen_time()),
            "server_time": time_provider.fmt(time_provider.now()),
        }
    )


@router.get("/requests")
def requests():
    return ok({"requests": debug_service.list_request_logs()})


@router.post("/punch/reset-today")
def reset_today_punch(body: ResetTodayPunchRequest | None = None, db: Session = Depends(get_db)):
    body = body or ResetTodayPunchRequest()
    deleted_count = punch_service.reset_today(db, username=body.username, user_id=body.user_id)
    return ok({"deleted_count": deleted_count}, msg="今日打卡已重置")


@router.post("/freeze-time")
def freeze_time(body: FreezeTimeRequest):
    value = datetime.strptime(body.datetime, "%Y-%m-%d %H:%M:%S")
    frozen = time_provider.freeze(value)
    return ok({"frozen_at": time_provider.fmt(frozen)}, msg="时间已冻结")


@router.delete("/freeze-time")
def unfreeze_time():
    time_provider.unfreeze()
    return ok(None, msg="时间已恢复")


def _today_range():
    current = time_provider.now()
    return (
        datetime.combine(current.date(), datetime.min.time()),
        datetime.combine(current.date(), datetime.max.time()),
    )
