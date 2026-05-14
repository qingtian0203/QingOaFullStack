from __future__ import annotations

import copy
import json
import math
from datetime import datetime, time, timedelta
from functools import lru_cache

from sqlalchemy import delete, func, or_, select
from sqlalchemy.orm import Session

from backend.core.config import DATA_DIR, EARLY_GRACE, LATE_GRACE, SHIFT_END, SHIFT_START
from backend.core import time_provider
from backend.core.errors import (
    APPEAL_DUPLICATED,
    APPEAL_REVIEW_FORBIDDEN,
    APPEAL_STATUS_INVALID,
    ApiError,
    CLOCK_IN_ALREADY_DONE,
    NO_CLOCK_IN,
    NO_PUNCH_PERMISSION,
    OUT_OF_RANGE,
    RESOURCE_NOT_FOUND,
    WORKFLOW_TASK_INVALID,
)
from backend.db.models import ProcessInstance, ProcessTask, PunchAppeal, PunchPoint, PunchRecord, User


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
        existing.status = attendance_status(punch_type, punch_time)
        existing.source = "manual"
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
    status: str | None = None,
    source: str = "manual",
    appeal_id: int | None = None,
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
        status=status or attendance_status(punch_type, punch_time),
        source=source,
        appeal_id=appeal_id,
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
        "status": record.status,
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
                "status": row.status,
                "status_label": status_label(row.status),
                "source": row.source,
                "appeal_id": row.appeal_id,
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
        "status": record.status,
        "status_label": status_label(record.status),
        "source": record.source,
        "appeal_id": record.appeal_id,
    }


def reset_today(
    db: Session,
    username: str | None = None,
    user_id: int | None = None,
    punch_date: str | None = None,
) -> int:
    query = delete(PunchRecord).where(PunchRecord.punch_date == (punch_date or current_punch_date()))
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


def attendance_status(punch_type: str, punch_time: datetime) -> str:
    current = punch_time.time()
    if punch_type == "clock_in":
        threshold = _time_with_delta(SHIFT_START, LATE_GRACE)
        return "late" if current > threshold else "normal"
    threshold = _time_with_delta(SHIFT_END, -EARLY_GRACE)
    return "early_leave" if current < threshold else "normal"


def _time_with_delta(value: str, minutes: int) -> time:
    base = datetime.strptime(value, "%H:%M")
    return (base + timedelta(minutes=minutes)).time()


def status_label(status: str | None) -> str:
    return {
        "normal": "正常",
        "late": "迟到",
        "early_leave": "早退",
        "missing_punch": "缺卡",
        "absent": "旷工",
        "makeup": "补卡",
    }.get(status or "", status or "未知")


def appeal_status_label(status: str | None) -> str:
    return {
        "submitted": "待上级审批",
        "manager_approved": "待 HR 审批",
        "approved": "已通过",
        "rejected_by_manager": "上级已驳回",
        "rejected_by_hr": "HR 已驳回",
    }.get(status or "", status or "未知")


def punch_type_label(punch_type: str | None) -> str:
    return "上班卡" if punch_type == "clock_in" else "下班卡"


def create_appeal(
    db: Session,
    user: User,
    punch_date: str,
    punch_type: str,
    reason: str,
    expect_time: str | None,
) -> dict:
    pending = db.scalar(
        select(PunchAppeal)
        .where(PunchAppeal.user_id == user.id)
        .where(PunchAppeal.punch_date == punch_date)
        .where(PunchAppeal.punch_type == punch_type)
        .where(PunchAppeal.status.in_(("submitted", "manager_approved")))
    )
    if pending is not None:
        raise ApiError(APPEAL_DUPLICATED, "该日期已有待审批申诉，不可重复提交")

    manager_id = user.manager_id
    if manager_id is None:
        manager = db.scalar(select(User).where(User.username == "manager"))
        manager_id = manager.id if manager else None
    if manager_id is None:
        raise ApiError(RESOURCE_NOT_FOUND, "未配置直属上级，无法提交申诉")

    appeal = PunchAppeal(
        user_id=user.id,
        punch_date=punch_date,
        punch_type=punch_type,
        reason=reason.strip(),
        expect_time=expect_time or default_expect_time(punch_type),
        status="submitted",
    )
    db.add(appeal)
    db.flush()

    instance = ProcessInstance(
        biz_type="punch_appeal",
        biz_id=appeal.id,
        title=f"补卡申诉：{punch_date} {punch_type_label(punch_type)}",
        applicant_id=user.id,
        status="running",
        current_node="manager_review",
    )
    db.add(instance)
    db.flush()
    appeal.process_instance_id = instance.id
    db.add(
        ProcessTask(
            instance_id=instance.id,
            node_key="manager_review",
            assignee_id=manager_id,
            status="todo",
        )
    )
    db.commit()
    db.refresh(appeal)
    return {"appeal_id": appeal.id, "status": appeal.status}


def my_appeals(db: Session, user: User) -> dict:
    rows = db.scalars(
        select(PunchAppeal)
        .where(PunchAppeal.user_id == user.id)
        .order_by(PunchAppeal.created_at.desc(), PunchAppeal.id.desc())
    ).all()
    return {"list": [_appeal_payload(db, row) for row in rows]}


def pending_review_appeals(db: Session, user: User) -> dict:
    tasks = db.scalars(
        select(ProcessTask)
        .where(ProcessTask.assignee_id == user.id)
        .where(ProcessTask.status == "todo")
        .order_by(ProcessTask.created_at.desc(), ProcessTask.id.desc())
    ).all()
    items = []
    for task in tasks:
        instance = db.get(ProcessInstance, task.instance_id)
        if instance is None or instance.biz_type != "punch_appeal":
            continue
        appeal = db.get(PunchAppeal, instance.biz_id)
        if appeal is not None:
            payload = _appeal_payload(db, appeal)
            payload["task_id"] = task.id
            payload["node_key"] = task.node_key
            payload["urged"] = bool(task.urged)
            items.append(payload)
    return {"list": items}


def review_appeal(db: Session, user: User, appeal_id: int, action: str, note: str | None) -> dict:
    appeal = db.get(PunchAppeal, appeal_id)
    if appeal is None:
        raise ApiError(RESOURCE_NOT_FOUND, "申诉不存在")
    instance = db.get(ProcessInstance, appeal.process_instance_id)
    if instance is None:
        raise ApiError(WORKFLOW_TASK_INVALID, "流程实例不存在")
    task = db.scalar(
        select(ProcessTask)
        .where(ProcessTask.instance_id == instance.id)
        .where(ProcessTask.status == "todo")
        .order_by(ProcessTask.id.desc())
    )
    if task is None:
        raise ApiError(WORKFLOW_TASK_INVALID, "流程任务不存在或已处理")
    if task.assignee_id != user.id:
        raise ApiError(APPEAL_REVIEW_FORBIDDEN, "无权限审批该申诉")

    now = time_provider.now()
    task.action = action
    task.note = note
    task.updated_at = now
    task.completed_at = now

    if task.node_key == "manager_review":
        if appeal.status != "submitted":
            raise ApiError(APPEAL_STATUS_INVALID, "申诉状态不允许上级审批")
        appeal.manager_note = note
        if action == "reject":
            appeal.status = "rejected_by_manager"
            task.status = "rejected"
            instance.status = "rejected"
            instance.current_node = None
        else:
            appeal.status = "manager_approved"
            task.status = "completed"
            instance.current_node = "hr_review"
            hr = db.scalar(select(User).where(User.is_hr == 1).order_by(User.id.asc()))
            if hr is None:
                raise ApiError(RESOURCE_NOT_FOUND, "未配置 HR 审批人")
            db.add(
                ProcessTask(
                    instance_id=instance.id,
                    node_key="hr_review",
                    assignee_id=hr.id,
                    status="todo",
                )
            )
    elif task.node_key == "hr_review":
        if appeal.status != "manager_approved":
            raise ApiError(APPEAL_STATUS_INVALID, "申诉状态不允许 HR 审批")
        appeal.hr_note = note
        if action == "reject":
            appeal.status = "rejected_by_hr"
            task.status = "rejected"
            instance.status = "rejected"
            instance.current_node = None
        else:
            appeal.status = "approved"
            task.status = "completed"
            instance.status = "completed"
            instance.current_node = None
            _upsert_makeup_record(db, appeal)
    else:
        raise ApiError(WORKFLOW_TASK_INVALID, "未知流程节点")

    appeal.updated_at = now
    instance.updated_at = now
    db.commit()
    db.refresh(appeal)
    return _appeal_payload(db, appeal)


def monthly_summary(db: Session, user: User, month: str | None = None) -> dict:
    month = month or time_provider.now().strftime("%Y-%m")
    rows = db.scalars(
        select(PunchRecord)
        .where(PunchRecord.user_id == user.id)
        .where(PunchRecord.punch_date.like(f"{month}-%"))
        .order_by(PunchRecord.punch_date.asc(), PunchRecord.punch_time.asc())
    ).all()
    by_date: dict[str, list[PunchRecord]] = {}
    for row in rows:
        by_date.setdefault(row.punch_date, []).append(row)

    late_count = sum(1 for row in rows if row.status == "late")
    early_leave_count = sum(1 for row in rows if row.status == "early_leave")
    missing_punch_count = 0
    normal_days = 0
    total_hours = 0.0
    for day_rows in by_date.values():
        clock_in = next((row for row in day_rows if row.punch_type == "clock_in"), None)
        clock_out = next((row for row in day_rows if row.punch_type == "clock_out"), None)
        if clock_in and clock_out:
            if clock_in.status in {"normal", "makeup"} and clock_out.status in {"normal", "makeup"}:
                normal_days += 1
            total_hours += max((clock_out.punch_time - clock_in.punch_time).total_seconds() / 3600, 0)
        else:
            missing_punch_count += 1
    return {
        "month": month,
        "normal_days": normal_days,
        "late_count": late_count,
        "early_leave_count": early_leave_count,
        "missing_punch_count": missing_punch_count,
        "total_work_hours": round(total_hours, 1),
    }


def workflow_tasks(db: Session, user: User, bucket: str = "todo") -> dict:
    query = select(ProcessTask).where(ProcessTask.assignee_id == user.id)
    if bucket == "todo":
        query = query.where(ProcessTask.status == "todo")
    elif bucket == "urged":
        query = query.where(ProcessTask.status == "todo").where(ProcessTask.urged == 1)
    elif bucket == "completed":
        query = query.where(ProcessTask.status != "todo")
    rows = db.scalars(query.order_by(ProcessTask.updated_at.desc(), ProcessTask.id.desc())).all()
    return {"tasks": [_task_payload(db, row) for row in rows]}


def workflow_templates(db: Session, user: User) -> dict:
    return {"templates": workflow_template_catalog()}


def workflow_template_catalog() -> list[dict]:
    return copy.deepcopy(_load_workflow_templates())


@lru_cache(maxsize=1)
def _load_workflow_templates() -> list[dict]:
    path = DATA_DIR / "workflow_templates.json"
    with path.open("r", encoding="utf-8") as fh:
        payload = json.load(fh)
    templates = payload.get("templates")
    if not isinstance(templates, list):
        raise RuntimeError("workflow_templates.json must contain a templates list")
    return templates


def workflow_instances(db: Session, user: User, bucket: str = "processing") -> dict:
    query = select(ProcessInstance)
    if bucket == "processing":
        query = query.where(ProcessInstance.applicant_id == user.id).where(ProcessInstance.status == "running")
    elif bucket == "returned":
        query = query.where(ProcessInstance.applicant_id == user.id).where(ProcessInstance.status == "returned")
    elif bucket == "completed":
        handled_instance_ids = select(ProcessTask.instance_id).where(ProcessTask.assignee_id == user.id)
        query = query.where(ProcessInstance.status.in_(("completed", "rejected", "cancelled"))).where(
            or_(ProcessInstance.applicant_id == user.id, ProcessInstance.id.in_(handled_instance_ids))
        )
    else:
        query = query.where(ProcessInstance.applicant_id == user.id)
    rows = db.scalars(query.order_by(ProcessInstance.updated_at.desc(), ProcessInstance.id.desc())).all()
    return {"instances": [_instance_payload(db, row) for row in rows]}


def workflow_instance_detail(db: Session, user: User, instance_id: int) -> dict:
    instance = db.get(ProcessInstance, instance_id)
    if instance is None:
        raise ApiError(RESOURCE_NOT_FOUND, "流程实例不存在")
    tasks = db.scalars(select(ProcessTask).where(ProcessTask.instance_id == instance.id)).all()
    if instance.applicant_id != user.id and all(task.assignee_id != user.id for task in tasks):
        raise ApiError(RESOURCE_NOT_FOUND, "流程实例不存在或无权限访问")
    payload = _instance_payload(db, instance)
    payload["timeline"] = [_task_payload(db, task) for task in tasks]
    if instance.biz_type == "punch_appeal":
        appeal = db.get(PunchAppeal, instance.biz_id)
        payload["business"] = _appeal_payload(db, appeal) if appeal else None
        payload["available_actions"] = []
    elif instance.biz_type == "leave_request":
        from backend.services import leave_service

        leave = db.get(leave_service.LeaveRequest, instance.biz_id)
        payload["business"] = leave_service.leave_payload(db, leave) if leave else None
        payload["available_actions"] = leave_service.available_actions(db, instance, user)
    return payload


def urge_instance(db: Session, user: User, instance_id: int) -> dict:
    instance = db.get(ProcessInstance, instance_id)
    if instance is None or instance.applicant_id != user.id:
        raise ApiError(RESOURCE_NOT_FOUND, "流程实例不存在或无权限访问")
    task = db.scalar(
        select(ProcessTask)
        .where(ProcessTask.instance_id == instance.id)
        .where(ProcessTask.status == "todo")
        .order_by(ProcessTask.id.desc())
    )
    if task is None:
        raise ApiError(WORKFLOW_TASK_INVALID, "当前没有可催办的待办任务")
    task.urged = 1
    task.updated_at = time_provider.now()
    db.commit()
    return {"task_id": task.id, "urged": True}


def review_workflow_task(db: Session, user: User, task_id: int, action: str, note: str | None) -> dict:
    task = db.get(ProcessTask, task_id)
    if task is None or task.status != "todo":
        raise ApiError(WORKFLOW_TASK_INVALID, "流程任务不存在或已处理")
    if task.assignee_id != user.id:
        raise ApiError(APPEAL_REVIEW_FORBIDDEN, "无权限处理该流程任务")
    instance = db.get(ProcessInstance, task.instance_id)
    if instance is None:
        raise ApiError(WORKFLOW_TASK_INVALID, "流程实例不存在")
    if instance.biz_type == "leave_request":
        from backend.services import leave_service

        return leave_service.review_leave_task(db, user, task, action, note)
    if instance.biz_type != "punch_appeal":
        raise ApiError(WORKFLOW_TASK_INVALID, "暂不支持该流程类型")
    appeal = db.get(PunchAppeal, instance.biz_id)
    if appeal is None:
        raise ApiError(RESOURCE_NOT_FOUND, "申诉不存在")
    return review_appeal(db, user, appeal.id, action, note)


def return_workflow_task(db: Session, user: User, task_id: int, note: str | None) -> dict:
    task = db.get(ProcessTask, task_id)
    if task is None or task.status != "todo":
        raise ApiError(WORKFLOW_TASK_INVALID, "流程任务不存在或已处理")
    if task.assignee_id != user.id:
        raise ApiError(APPEAL_REVIEW_FORBIDDEN, "无权限处理该流程任务")
    instance = db.get(ProcessInstance, task.instance_id)
    if instance is None:
        raise ApiError(WORKFLOW_TASK_INVALID, "流程实例不存在")
    if instance.biz_type == "leave_request":
        from backend.services import leave_service

        return leave_service.return_leave_task(db, user, task, note)
    raise ApiError(WORKFLOW_TASK_INVALID, "当前流程不支持退回修改")


def resubmit_workflow_instance(db: Session, user: User, instance_id: int, body) -> dict:
    instance = db.get(ProcessInstance, instance_id)
    if instance is None:
        raise ApiError(RESOURCE_NOT_FOUND, "流程实例不存在")
    if instance.biz_type == "leave_request":
        from backend.services import leave_service

        return leave_service.resubmit_leave_instance(db, user, instance_id, body)
    raise ApiError(WORKFLOW_TASK_INVALID, "当前流程不支持重新提交")


def default_expect_time(punch_type: str) -> str:
    return "09:00:00" if punch_type == "clock_in" else "18:00:00"


def _upsert_makeup_record(db: Session, appeal: PunchAppeal) -> None:
    point = db.scalar(select(PunchPoint).where(PunchPoint.is_active == 1).order_by(PunchPoint.id.asc()))
    if point is None:
        raise ApiError(OUT_OF_RANGE, "没有可用打卡点，无法生成补卡记录")
    punch_time = datetime.strptime(f"{appeal.punch_date} {appeal.expect_time or default_expect_time(appeal.punch_type)}", "%Y-%m-%d %H:%M:%S")
    existing = db.scalar(
        select(PunchRecord)
        .where(PunchRecord.user_id == appeal.user_id)
        .where(PunchRecord.punch_date == appeal.punch_date)
        .where(PunchRecord.punch_type == appeal.punch_type)
    )
    if existing:
        existing.punch_point_id = point.id
        existing.punch_time = punch_time
        existing.lat = point.lat
        existing.lng = point.lng
        existing.distance = 0
        existing.device_id = "appeal"
        existing.status = "makeup"
        existing.source = "appeal"
        existing.appeal_id = appeal.id
        return
    _create_record(
        db,
        db.get(User, appeal.user_id),
        point,
        appeal.punch_type,
        appeal.punch_date,
        punch_time,
        point.lat,
        point.lng,
        0,
        "appeal",
        status="makeup",
        source="appeal",
        appeal_id=appeal.id,
    )


def _appeal_payload(db: Session, appeal: PunchAppeal) -> dict:
    user = db.get(User, appeal.user_id)
    return {
        "id": appeal.id,
        "user_id": appeal.user_id,
        "username": user.username if user else "",
        "applicant_name": user.name if user else "",
        "process_instance_id": appeal.process_instance_id,
        "punch_date": appeal.punch_date,
        "punch_type": appeal.punch_type,
        "punch_type_label": punch_type_label(appeal.punch_type),
        "reason": appeal.reason,
        "expect_time": appeal.expect_time,
        "status": appeal.status,
        "status_label": appeal_status_label(appeal.status),
        "manager_note": appeal.manager_note,
        "hr_note": appeal.hr_note,
        "created_at": time_provider.fmt(appeal.created_at),
        "updated_at": time_provider.fmt(appeal.updated_at),
    }


def _task_payload(db: Session, task: ProcessTask) -> dict:
    instance = db.get(ProcessInstance, task.instance_id)
    assignee = db.get(User, task.assignee_id)
    applicant = db.get(User, instance.applicant_id) if instance else None
    return {
        "id": task.id,
        "instance_id": task.instance_id,
        "biz_type": instance.biz_type if instance else "",
        "biz_id": instance.biz_id if instance else None,
        "title": instance.title if instance else "",
        "instance_status": instance.status if instance else "",
        "current_node": instance.current_node if instance else None,
        "applicant_id": instance.applicant_id if instance else None,
        "applicant_name": applicant.name if applicant else "",
        "node_key": task.node_key,
        "assignee_id": task.assignee_id,
        "assignee_name": assignee.name if assignee else "",
        "status": task.status,
        "urged": bool(task.urged),
        "action": task.action,
        "note": task.note,
        "created_at": time_provider.fmt(task.created_at),
        "updated_at": time_provider.fmt(task.updated_at),
        "completed_at": time_provider.fmt(task.completed_at),
    }


def _instance_payload(db: Session, instance: ProcessInstance) -> dict:
    applicant = db.get(User, instance.applicant_id)
    return {
        "id": instance.id,
        "biz_type": instance.biz_type,
        "biz_id": instance.biz_id,
        "title": instance.title,
        "applicant_id": instance.applicant_id,
        "applicant_name": applicant.name if applicant else "",
        "status": instance.status,
        "current_node": instance.current_node,
        "created_at": time_provider.fmt(instance.created_at),
        "updated_at": time_provider.fmt(instance.updated_at),
    }
