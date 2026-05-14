from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from backend.core import time_provider
from backend.core.response import ok
from backend.db.database import create_tables, get_db
from backend.db.models import (
    KeyResult,
    LeaveAttachment,
    LeaveRequest,
    NoticeRead,
    Okr,
    ProcessInstance,
    ProcessTask,
    PunchAppeal,
    PunchRecord,
    UploadedFile,
    User,
)
from backend.db.seed import reset_database, seed_okrs
from backend.schemas.debug import (
    FreezeTimeRequest,
    ResetNoticeReadRequest,
    ResetOkrRequest,
    ResetProfileRequest,
    ResetImRequest,
    RecalculateAttendanceRequest,
    ResetTodayPunchRequest,
    ScenarioRequest,
)
from backend.services import debug_service, im_service, leave_service, punch_service

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
    notice_reads = db.scalars(select(NoticeRead).order_by(NoticeRead.id.asc())).all()
    appeals = db.scalars(select(PunchAppeal).order_by(PunchAppeal.id.asc())).all()
    leaves = db.scalars(select(LeaveRequest).order_by(LeaveRequest.id.asc())).all()
    instances = db.scalars(select(ProcessInstance).order_by(ProcessInstance.id.asc())).all()
    tasks = db.scalars(select(ProcessTask).order_by(ProcessTask.id.asc())).all()
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
                    "status": row.status,
                    "source": row.source,
                    "appeal_id": row.appeal_id,
                }
                for row in today_records
            ],
            "punch_appeals": [
                {
                    "id": row.id,
                    "user_id": row.user_id,
                    "punch_date": row.punch_date,
                    "punch_type": row.punch_type,
                    "status": row.status,
                    "process_instance_id": row.process_instance_id,
                }
                for row in appeals
            ],
            "leave_requests": [
                {
                    "id": row.id,
                    "user_id": row.user_id,
                    "process_instance_id": row.process_instance_id,
                    "leave_type": row.leave_type,
                    "start_date": row.start_date,
                    "end_date": row.end_date,
                    "days": row.days,
                    "status": row.status,
                    "attachments": leave_service.leave_attachments_payload(db, row.id),
                }
                for row in leaves
            ],
            "process_instances": [
                {
                    "id": row.id,
                    "biz_type": row.biz_type,
                    "biz_id": row.biz_id,
                    "applicant_id": row.applicant_id,
                    "status": row.status,
                    "current_node": row.current_node,
                }
                for row in instances
            ],
            "process_tasks": [
                {
                    "id": row.id,
                    "instance_id": row.instance_id,
                    "node_key": row.node_key,
                    "assignee_id": row.assignee_id,
                    "status": row.status,
                    "urged": bool(row.urged),
                    "action": row.action,
                }
                for row in tasks
            ],
            "active_scenarios": debug_service.list_scenarios(),
            "notice_reads": [
                {
                    "notice_id": row.notice_id,
                    "user_id": row.user_id,
                    "read_at": time_provider.fmt(row.read_at),
                }
                for row in notice_reads
            ],
            "frozen_time": time_provider.fmt(time_provider.frozen_time()),
            "server_time": time_provider.fmt(time_provider.now()),
        }
    )


@router.get("/requests")
def requests():
    return ok({"requests": debug_service.list_request_logs()})


@router.get("/attendance/latest")
def latest_attendance(
    username: str | None = Query(None),
    user_id: int | None = Query(None),
    punch_type: str | None = Query(None),
    punch_date: str | None = Query(None),
    db: Session = Depends(get_db),
):
    target_user: User | None = None
    if username:
        target_user = db.scalar(select(User).where(User.username == username))
    elif user_id is not None:
        target_user = db.scalar(select(User).where(User.id == user_id))

    if (username or user_id is not None) and target_user is None:
        return ok(
            {
                "query": {
                    "username": username,
                    "user_id": user_id,
                    "punch_type": punch_type,
                    "punch_date": punch_date,
                },
                "user": None,
                "record": None,
            },
            msg="用户不存在",
        )

    target_date = punch_date or time_provider.now().date().isoformat()
    stmt = select(PunchRecord).where(PunchRecord.punch_date == target_date)
    if target_user is not None:
        stmt = stmt.where(PunchRecord.user_id == target_user.id)
    if punch_type:
        stmt = stmt.where(PunchRecord.punch_type == punch_type)
    record = db.scalar(stmt.order_by(PunchRecord.punch_time.desc(), PunchRecord.id.desc()))

    if record is not None and target_user is None:
        target_user = db.scalar(select(User).where(User.id == record.user_id))

    return ok(
        {
            "query": {
                "username": username,
                "user_id": user_id,
                "punch_type": punch_type,
                "punch_date": target_date,
            },
            "user": _debug_user(target_user),
            "record": _debug_punch_record(record),
        }
    )


@router.get("/leave/latest")
def latest_leave(
    username: str | None = Query(None),
    user_id: int | None = Query(None),
    db: Session = Depends(get_db),
):
    return ok(leave_service.latest_leave(db, username=username, user_id=user_id))


@router.get("/workflow/state")
def workflow_state(
    username: str | None = Query(None),
    db: Session = Depends(get_db),
):
    user_id: int | None = None
    if username:
        user = db.scalar(select(User).where(User.username == username))
        user_id = user.id if user else -1
    instances = db.scalars(select(ProcessInstance).order_by(ProcessInstance.id.asc())).all()
    tasks = db.scalars(select(ProcessTask).order_by(ProcessTask.id.asc())).all()
    appeals = db.scalars(select(PunchAppeal).order_by(PunchAppeal.id.asc())).all()
    leaves = db.scalars(select(LeaveRequest).order_by(LeaveRequest.id.asc())).all()
    if user_id is not None:
        instance_ids = {row.id for row in instances if row.applicant_id == user_id}
        instance_ids.update(row.instance_id for row in tasks if row.assignee_id == user_id)
        appeal_ids = {row.biz_id for row in instances if row.id in instance_ids and row.biz_type == "punch_appeal"}
        leave_ids = {row.biz_id for row in instances if row.id in instance_ids and row.biz_type == "leave_request"}
        instances = [row for row in instances if row.id in instance_ids]
        tasks = [row for row in tasks if row.instance_id in instance_ids]
        appeals = [row for row in appeals if row.id in appeal_ids or row.user_id == user_id]
        leaves = [row for row in leaves if row.id in leave_ids or row.user_id == user_id]
    templates = punch_service.workflow_template_catalog()
    return ok(
        {
            "templates": templates,
            "instances": [
                {
                    "id": row.id,
                    "biz_type": row.biz_type,
                    "biz_id": row.biz_id,
                    "title": row.title,
                    "applicant_id": row.applicant_id,
                    "status": row.status,
                    "current_node": row.current_node,
                    "created_at": time_provider.fmt(row.created_at),
                    "updated_at": time_provider.fmt(row.updated_at),
                }
                for row in instances
            ],
            "tasks": [
                {
                    "id": row.id,
                    "instance_id": row.instance_id,
                    "node_key": row.node_key,
                    "assignee_id": row.assignee_id,
                    "status": row.status,
                    "urged": bool(row.urged),
                    "action": row.action,
                    "note": row.note,
                    "created_at": time_provider.fmt(row.created_at),
                    "updated_at": time_provider.fmt(row.updated_at),
                    "completed_at": time_provider.fmt(row.completed_at),
                }
                for row in tasks
            ],
            "instance_nodes": _workflow_instance_nodes(instances, tasks, templates),
            "punch_appeals": [
                {
                    "id": row.id,
                    "user_id": row.user_id,
                    "process_instance_id": row.process_instance_id,
                    "punch_date": row.punch_date,
                    "punch_type": row.punch_type,
                    "status": row.status,
                    "expect_time": row.expect_time,
                    "manager_note": row.manager_note,
                    "hr_note": row.hr_note,
                    "created_at": time_provider.fmt(row.created_at),
                    "updated_at": time_provider.fmt(row.updated_at),
                }
                for row in appeals
            ],
            "leave_requests": [
                {
                    "id": row.id,
                    "user_id": row.user_id,
                    "process_instance_id": row.process_instance_id,
                    "leave_type": row.leave_type,
                    "start_date": row.start_date,
                    "end_date": row.end_date,
                    "days": row.days,
                    "status": row.status,
                    "return_reason": row.return_reason,
                    "attachments": leave_service.leave_attachments_payload(db, row.id),
                    "created_at": time_provider.fmt(row.created_at),
                    "updated_at": time_provider.fmt(row.updated_at),
                }
                for row in leaves
            ],
        }
    )


@router.get("/workflow/templates")
def workflow_templates():
    templates = punch_service.workflow_template_catalog()
    return ok({"templates": templates, "template_count": len(templates)})


@router.post("/im/reset")
def reset_im(body: ResetImRequest | None = None, db: Session = Depends(get_db)):
    body = body or ResetImRequest()
    result = im_service.debug_reset(db, usernames=body.usernames, user_ids=body.user_ids)
    return ok(result, msg="IM 测试状态已重置")


@router.get("/im/state")
def im_state(username: str | None = Query(None), db: Session = Depends(get_db)):
    return ok(im_service.debug_state(db, username=username))


@router.post("/workflow/reset")
def reset_workflow_state(
    username: str | None = Query(None),
    db: Session = Depends(get_db),
):
    user_id: int | None = None
    if username:
        user = db.scalar(select(User).where(User.username == username))
        if user is None:
            return ok({"deleted_count": 0, "username": username}, msg="用户不存在")
        user_id = user.id

    if user_id is None:
        instance_ids = list(db.scalars(select(ProcessInstance.id)).all())
        db.execute(delete(ProcessTask))
        db.execute(delete(PunchAppeal))
        db.execute(delete(LeaveAttachment))
        db.execute(delete(LeaveRequest))
        db.execute(delete(ProcessInstance))
    else:
        instances = db.scalars(select(ProcessInstance).where(ProcessInstance.applicant_id == user_id)).all()
        instance_ids = [row.id for row in instances]
        if instance_ids:
            db.execute(delete(ProcessTask).where(ProcessTask.instance_id.in_(instance_ids)))
        db.execute(delete(PunchAppeal).where(PunchAppeal.user_id == user_id))
        leave_ids = list(db.scalars(select(LeaveRequest.id).where(LeaveRequest.user_id == user_id)).all())
        if leave_ids:
            db.execute(delete(LeaveAttachment).where(LeaveAttachment.leave_id.in_(leave_ids)))
        db.execute(delete(LeaveRequest).where(LeaveRequest.user_id == user_id))
        if instance_ids:
            db.execute(delete(ProcessInstance).where(ProcessInstance.id.in_(instance_ids)))

    db.commit()
    return ok({"deleted_count": len(instance_ids), "username": username}, msg="流程状态已重置")


def _workflow_instance_nodes(
    instances: list[ProcessInstance],
    tasks: list[ProcessTask],
    templates: list[dict],
) -> list[dict]:
    template_by_biz = {row.get("biz_type"): row for row in templates if row.get("biz_type")}
    instance_by_id = {row.id: row for row in instances}
    rows: list[dict] = []
    for task in tasks:
        instance = instance_by_id.get(task.instance_id)
        if instance is None:
            continue
        template = template_by_biz.get(instance.biz_type, {})
        node = _workflow_template_node(template, task.node_key)
        rows.append(
            {
                "instance_id": task.instance_id,
                "biz_type": instance.biz_type,
                "biz_id": instance.biz_id,
                "template_id": template.get("id"),
                "node_key": task.node_key,
                "node_title": node.get("title", task.node_key),
                "assignee_role": node.get("assignee_role", ""),
                "actions": node.get("actions", []),
                "task_id": task.id,
                "task_status": task.status,
                "current": instance.current_node == task.node_key and task.status == "todo",
            }
        )
    return rows


def _workflow_template_node(template: dict, node_key: str) -> dict:
    for node in template.get("nodes") or []:
        if node.get("key") == node_key:
            return node
    return {}


@router.post("/punch/reset-today")
def reset_today_punch(body: ResetTodayPunchRequest | None = None, db: Session = Depends(get_db)):
    body = body or ResetTodayPunchRequest()
    deleted_count = punch_service.reset_today(
        db,
        username=body.username,
        user_id=body.user_id,
        punch_date=body.punch_date,
    )
    return ok(
        {
            "deleted_count": deleted_count,
            "username": body.username,
            "user_id": body.user_id,
            "punch_date": body.punch_date or time_provider.now().date().isoformat(),
        },
        msg="打卡记录已重置",
    )


@router.post("/notices/reset-read")
def reset_notice_reads(body: ResetNoticeReadRequest | None = None, db: Session = Depends(get_db)):
    body = body or ResetNoticeReadRequest()
    user_id = body.user_id
    if body.username:
        user = db.scalar(select(User).where(User.username == body.username))
        if user is None:
            return ok({"deleted_count": 0, "username": body.username}, msg="用户不存在")
        user_id = user.id

    query = delete(NoticeRead)
    if user_id is not None:
        query = query.where(NoticeRead.user_id == user_id)
    if body.notice_id is not None:
        query = query.where(NoticeRead.notice_id == body.notice_id)
    result = db.execute(query)
    db.commit()
    return ok(
        {
            "deleted_count": result.rowcount or 0,
            "username": body.username,
            "user_id": user_id,
            "notice_id": body.notice_id,
        },
        msg="公告已读状态已重置",
    )


@router.post("/okr/reset")
def reset_okrs(body: ResetOkrRequest | None = None, db: Session = Depends(get_db)):
    body = body or ResetOkrRequest()
    users = _debug_target_users(db, usernames=body.usernames, user_ids=body.user_ids)
    user_ids = [user.id for user in users]
    if not user_ids:
        return ok({"deleted_count": 0, "usernames": body.usernames, "user_ids": body.user_ids}, msg="用户不存在")

    okr_ids = list(db.scalars(select(Okr.id).where(Okr.user_id.in_(user_ids))).all())
    if okr_ids:
        db.execute(delete(KeyResult).where(KeyResult.okr_id.in_(okr_ids)))
        db.execute(delete(Okr).where(Okr.id.in_(okr_ids)))
    seed_okrs(db, users)
    db.commit()
    return ok(
        {
            "deleted_count": len(okr_ids),
            "seeded_usernames": [user.username for user in users],
        },
        msg="OKR 种子数据已重置",
    )


@router.post("/profile/reset")
def reset_profile(body: ResetProfileRequest | None = None, db: Session = Depends(get_db)):
    body = body or ResetProfileRequest()
    users = _debug_target_users(
        db,
        usernames=[body.username] if body.username else None,
        user_ids=[body.user_id] if body.user_id is not None else None,
    )
    if not users:
        return ok({"updated_count": 0, "username": body.username, "user_id": body.user_id}, msg="用户不存在")
    user = users[0]
    user.avatar_url = body.avatar_url
    upload_result = db.execute(
        delete(UploadedFile)
        .where(UploadedFile.uploaded_by == user.id)
        .where(UploadedFile.usage == "avatar")
    )
    db.commit()
    return ok(
        {
            "updated_count": 1,
            "deleted_upload_count": upload_result.rowcount or 0,
            "username": user.username,
            "avatar_url": user.avatar_url or "",
        },
        msg="用户资料测试状态已重置",
    )


@router.post("/attendance/recalculate")
def recalculate_attendance(body: RecalculateAttendanceRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.username == body.username))
    if user is None:
        return ok({"month": body.month, "summary": None}, msg="用户不存在")
    return ok(
        {
            "username": body.username,
            "month": body.month,
            "summary": punch_service.monthly_summary(db, user, body.month),
        },
        msg="考勤状态已重算",
    )


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


def _debug_target_users(
    db: Session,
    *,
    usernames: list[str] | None = None,
    user_ids: list[int] | None = None,
) -> list[User]:
    names = [item for item in (usernames or []) if item]
    ids = [item for item in (user_ids or []) if item is not None]
    query = select(User).order_by(User.id.asc())
    if names and ids:
        query = query.where((User.username.in_(names)) | (User.id.in_(ids)))
    elif names:
        query = query.where(User.username.in_(names))
    elif ids:
        query = query.where(User.id.in_(ids))
    return list(db.scalars(query).all())


def _debug_user(user: User | None) -> dict | None:
    if user is None:
        return None
    return {
        "id": user.id,
        "username": user.username,
        "name": user.name,
        "dept": user.dept,
        "role": user.role,
    }


def _debug_punch_record(record: PunchRecord | None) -> dict | None:
    if record is None:
        return None
    point = record.punch_point
    return {
        "id": record.id,
        "user_id": record.user_id,
        "punch_point_id": record.punch_point_id,
        "punch_type": record.punch_type,
        "punch_date": record.punch_date,
        "punch_time": time_provider.fmt(record.punch_time),
        "lat": record.lat,
        "lng": record.lng,
        "distance": record.distance,
        "device_id": record.device_id,
        "status": record.status,
        "source": record.source,
        "appeal_id": record.appeal_id,
        "point_name": point.name if point else None,
        "created_at": time_provider.fmt(record.created_at),
    }
