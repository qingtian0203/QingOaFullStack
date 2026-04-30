from __future__ import annotations

import math
from datetime import datetime, time

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from backend.core import time_provider
from backend.core.errors import (
    ApiError,
    CLOCK_IN_ALREADY_DONE,
    NO_CLOCK_IN,
    NO_PUNCH_PERMISSION,
    OUT_OF_RANGE,
    RESOURCE_NOT_FOUND,
)
from backend.db.models import PunchPoint, PunchRecord, User


def today_range() -> tuple[datetime, datetime]:
    current = time_provider.now()
    start = datetime.combine(current.date(), time.min)
    end = datetime.combine(current.date(), time.max)
    return start, end


def current_punch_date() -> str:
    return time_provider.now().date().isoformat()


def today_record(db: Session, user: User, punch_type: str = "clock_in") -> PunchRecord | None:
    return db.scalar(
        select(PunchRecord)
        .where(PunchRecord.user_id == user.id)
        .where(PunchRecord.punch_date == current_punch_date())
        .where(PunchRecord.punch_type == punch_type)
        .order_by(PunchRecord.punch_time.desc())
    )


def today_status(db: Session, user: User) -> dict:
    clock_in_record = today_record(db, user, "clock_in")
    clock_out_record = today_record(db, user, "clock_out")
    points = db.scalars(
        select(PunchPoint).where(PunchPoint.is_active == 1).order_by(PunchPoint.id.asc())
    ).all()
    return {
        "clock_in": _today_status_item(clock_in_record),
        "clock_out": _today_status_item(clock_out_record),
        "punch_points": [
            {"id": point.id, "name": point.name, "lat": point.lat, "lng": point.lng, "radius": point.radius}
            for point in points
        ],
        # v1 兼容字段：旧 App 只关心是否已有任意打卡。
        "has_punched": clock_in_record is not None or clock_out_record is not None,
        "punch_time": time_provider.fmt((clock_out_record or clock_in_record).punch_time)
        if (clock_out_record or clock_in_record)
        else None,
    }


def clock_in(db: Session, user: User, lat: float, lng: float, device_id: str | None) -> dict:
    # v1 deprecated 兼容：首次走上班卡；已有上班卡后再点旧按钮则写/更新下班卡。
    punch_type = "clock_out" if today_record(db, user, "clock_in") else "clock_in"
    return clock(db, user, lat, lng, device_id, punch_type)


def clock(db: Session, user: User, lat: float, lng: float, device_id: str | None, punch_type: str) -> dict:
    if not user.has_punch_permission:
        raise ApiError(NO_PUNCH_PERMISSION, "您没有打卡权限")

    point, distance = nearest_active_point(db, lat, lng)
    if point is None:
        raise ApiError(OUT_OF_RANGE, "不在打卡范围内（没有可用打卡点）")
    if distance > point.radius:
        raise ApiError(
            OUT_OF_RANGE,
            f"不在打卡范围内（距离 {distance} 米，超出 {point.radius} 米限制）",
        )

    punch_time = time_provider.now()
    punch_date = current_punch_date()

    if punch_type == "clock_in":
        existing = today_record(db, user, "clock_in")
        if existing is not None:
            raise ApiError(CLOCK_IN_ALREADY_DONE, "今日上班卡已打，不可重复")
        record = _create_record(db, user, point, punch_type, punch_date, punch_time, lat, lng, distance, device_id)
        return _punch_payload(record, point.name, updated=False)

    if punch_type == "clock_out" and today_record(db, user, "clock_in") is None:
        raise ApiError(NO_CLOCK_IN, "未打上班卡，不能打下班卡")

    existing = today_record(db, user, "clock_out")
    if existing is not None:
        existing.punch_point_id = point.id
        existing.punch_time = punch_time
        existing.punch_date = punch_date
        existing.punch_type = punch_type
        existing.lat = lat
        existing.lng = lng
        existing.distance = distance
        existing.device_id = device_id
        db.commit()
        db.refresh(existing)
        return _punch_payload(existing, point.name, updated=True)

    record = _create_record(db, user, point, punch_type, punch_date, punch_time, lat, lng, distance, device_id)
    return _punch_payload(record, point.name, updated=False)


def _create_record(
    db: Session,
    user: User,
    point: PunchPoint,
    punch_type: str,
    punch_date: str,
    punch_time: datetime,
    lat: float,
    lng: float,
    distance: int,
    device_id: str | None,
) -> PunchRecord:
    record = PunchRecord(
        user_id=user.id,
        punch_point_id=point.id,
        punch_type=punch_type,
        punch_date=punch_date,
        punch_time=punch_time,
        lat=lat,
        lng=lng,
        distance=distance,
        device_id=device_id,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def _punch_payload(record: PunchRecord, point_name: str, updated: bool) -> dict:
    return {
        "punch_id": record.id,
        "punch_time": time_provider.fmt(record.punch_time),
        "distance": record.distance,
        "point_name": point_name,
        "updated": updated,
    }


def records(db: Session, user: User, page: int, size: int) -> dict:
    page = max(page, 1)
    size = max(min(size, 100), 1)
    query = select(PunchRecord).where(PunchRecord.user_id == user.id)
    total = db.scalar(select(func.count(PunchRecord.id)).where(PunchRecord.user_id == user.id)) or 0
    rows = db.scalars(
        query.order_by(PunchRecord.punch_time.desc()).offset((page - 1) * size).limit(size)
    ).all()
    return {
        "total": total,
        "page": page,
        "size": size,
        "list": [
            {
                "id": row.id,
                "punch_type": row.punch_type,
                "punch_date": row.punch_date,
                "punch_time": time_provider.fmt(row.punch_time),
                "point_name": row.punch_point.name,
                "distance": row.distance,
                "status": "正常",
            }
            for row in rows
        ],
    }


def record_detail(db: Session, user: User, record_id: int) -> dict:
    record = db.get(PunchRecord, record_id)
    if record is None or record.user_id != user.id:
        raise ApiError(RESOURCE_NOT_FOUND, "打卡记录不存在或无权限访问")
    return {
        "id": record.id,
        "punch_type": record.punch_type,
        "punch_date": record.punch_date,
        "punch_time": time_provider.fmt(record.punch_time),
        "point_name": record.punch_point.name,
        "lat": record.lat,
        "lng": record.lng,
        "distance": record.distance,
        "device_id": record.device_id,
    }


def reset_today(db: Session, username: str | None = None, user_id: int | None = None) -> int:
    query = delete(PunchRecord).where(PunchRecord.punch_date == current_punch_date())
    if username:
        user = db.scalar(select(User).where(User.username == username))
        if user is None:
            return 0
        query = query.where(PunchRecord.user_id == user.id)
    elif user_id is not None:
        query = query.where(PunchRecord.user_id == user_id)
    result = db.execute(query)
    db.commit()
    return result.rowcount or 0


def _today_status_item(record: PunchRecord | None) -> dict:
    return {
        "done": record is not None,
        "punch_id": record.id if record else None,
        "time": record.punch_time.strftime("%H:%M:%S") if record else None,
    }


def nearest_active_point(db: Session, lat: float, lng: float) -> tuple[PunchPoint | None, int]:
    points = db.scalars(select(PunchPoint).where(PunchPoint.is_active == 1)).all()
    if not points:
        return None, 0
    distances = [(point, haversine_meters(lat, lng, point.lat, point.lng)) for point in points]
    point, distance = min(distances, key=lambda item: item[1])
    return point, distance


def haversine_meters(lat1: float, lng1: float, lat2: float, lng2: float) -> int:
    radius = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lng2 - lng1)
    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return int(round(radius * c))
