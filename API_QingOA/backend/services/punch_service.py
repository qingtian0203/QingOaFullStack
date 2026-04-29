from __future__ import annotations

import math
from datetime import datetime, time

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.core import time_provider
from backend.core.errors import (
    ALREADY_PUNCHED,
    ApiError,
    NO_PUNCH_PERMISSION,
    OUT_OF_RANGE,
)
from backend.db.models import PunchPoint, PunchRecord, User


def today_range() -> tuple[datetime, datetime]:
    current = time_provider.now()
    start = datetime.combine(current.date(), time.min)
    end = datetime.combine(current.date(), time.max)
    return start, end


def today_record(db: Session, user: User) -> PunchRecord | None:
    start, end = today_range()
    return db.scalar(
        select(PunchRecord)
        .where(PunchRecord.user_id == user.id)
        .where(PunchRecord.punch_time >= start)
        .where(PunchRecord.punch_time <= end)
        .order_by(PunchRecord.punch_time.desc())
    )


def today_status(db: Session, user: User) -> dict:
    record = today_record(db, user)
    points = db.scalars(
        select(PunchPoint).where(PunchPoint.is_active == 1).order_by(PunchPoint.id.asc())
    ).all()
    return {
        "has_punched": record is not None,
        "punch_time": time_provider.fmt(record.punch_time) if record else None,
        "punch_points": [
            {"id": point.id, "name": point.name, "lat": point.lat, "lng": point.lng, "radius": point.radius}
            for point in points
        ],
    }


def clock_in(db: Session, user: User, lat: float, lng: float, device_id: str | None) -> dict:
    if not user.has_punch_permission:
        raise ApiError(NO_PUNCH_PERMISSION, "您没有打卡权限")

    existing = today_record(db, user)
    if existing is not None:
        raise ApiError(ALREADY_PUNCHED, f"今日已打卡（{existing.punch_time.strftime('%H:%M:%S')}）")

    point, distance = nearest_active_point(db, lat, lng)
    if point is None:
        raise ApiError(OUT_OF_RANGE, "不在打卡范围内（没有可用打卡点）")
    if distance > point.radius:
        raise ApiError(
            OUT_OF_RANGE,
            f"不在打卡范围内（距离 {distance} 米，超出 {point.radius} 米限制）",
        )

    punch_time = time_provider.now()
    record = PunchRecord(
        user_id=user.id,
        punch_point_id=point.id,
        punch_time=punch_time,
        lat=lat,
        lng=lng,
        distance=distance,
        device_id=device_id,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return {
        "punch_id": record.id,
        "punch_time": time_provider.fmt(record.punch_time),
        "distance": record.distance,
        "point_name": point.name,
    }


def records(db: Session, user: User, page: int, size: int) -> dict:
    page = max(page, 1)
    size = max(min(size, 100), 1)
    query = select(PunchRecord).where(PunchRecord.user_id == user.id)
    total = len(db.scalars(query).all())
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
                "punch_time": time_provider.fmt(row.punch_time),
                "point_name": row.punch_point.name,
                "distance": row.distance,
                "status": "正常",
            }
            for row in rows
        ],
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

