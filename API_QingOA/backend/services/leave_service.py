from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.core import time_provider
from backend.core.config import LEAVE_HR_REVIEW_THRESHOLD_DAYS
from backend.core.errors import (
    APPEAL_REVIEW_FORBIDDEN,
    APPEAL_STATUS_INVALID,
    ApiError,
    FILE_UPLOAD_INVALID,
    LEAVE_DATE_INVALID,
    LEAVE_DAYS_INVALID,
    LEAVE_RESUBMIT_FORBIDDEN,
    LEAVE_RETURN_FORBIDDEN,
    LEAVE_TYPE_INVALID,
    RESOURCE_NOT_FOUND,
    WORKFLOW_TASK_INVALID,
)
from backend.db.models import LeaveAttachment, LeaveRequest, ProcessInstance, ProcessTask, UploadedFile, User
from backend.schemas.leave import LeaveCreateRequest, LeaveResubmitRequest
from backend.services import file_service


LEAVE_TYPE_LABELS = {
    "annual": "年假",
    "sick": "病假",
    "personal": "事假",
}


def create_leave_request(db: Session, user: User, body: LeaveCreateRequest) -> dict:
    leave_type, start_date, end_date, days = _validated_leave_values(body)
    attachment_files = _validated_attachment_files(db, user, body.attachment_file_ids)
    manager_id = _manager_id(db, user)
    now = time_provider.now()
    leave = LeaveRequest(
        user_id=user.id,
        leave_type=leave_type,
        start_date=start_date,
        end_date=end_date,
        days=days,
        reason=body.reason.strip(),
        status="submitted",
        created_at=now,
        updated_at=now,
    )
    db.add(leave)
    db.flush()
    _replace_leave_attachments(db, leave.id, attachment_files, now)

    instance = ProcessInstance(
        biz_type="leave_request",
        biz_id=leave.id,
        title=f"请假申请：{LEAVE_TYPE_LABELS[leave.leave_type]} {leave.start_date} 至 {leave.end_date}",
        applicant_id=user.id,
        status="running",
        current_node="manager_review",
        created_at=now,
        updated_at=now,
    )
    db.add(instance)
    db.flush()
    leave.process_instance_id = instance.id
    db.add(
        ProcessTask(
            instance_id=instance.id,
            node_key="manager_review",
            assignee_id=manager_id,
            status="todo",
            created_at=now,
            updated_at=now,
        )
    )
    db.commit()
    db.refresh(leave)
    return leave_payload(db, leave)


def cancel_leave_request(db: Session, user: User, leave_id: int) -> dict:
    leave = db.get(LeaveRequest, leave_id)
    if leave is None or leave.user_id != user.id:
        raise ApiError(RESOURCE_NOT_FOUND, "请假申请不存在或无权限访问")
    if leave.status in {"approved", "rejected", "cancelled"}:
        raise ApiError(APPEAL_STATUS_INVALID, "当前状态不允许取消")
    instance = db.get(ProcessInstance, leave.process_instance_id)
    now = time_provider.now()
    leave.status = "cancelled"
    leave.updated_at = now
    if instance is not None:
        instance.status = "cancelled"
        instance.current_node = None
        instance.updated_at = now
        tasks = db.scalars(
            select(ProcessTask).where(ProcessTask.instance_id == instance.id).where(ProcessTask.status == "todo")
        ).all()
        for task in tasks:
            task.status = "cancelled"
            task.action = "cancel"
            task.updated_at = now
            task.completed_at = now
    db.commit()
    db.refresh(leave)
    return leave_payload(db, leave)


def review_leave_task(db: Session, user: User, task: ProcessTask, action: str, note: str | None) -> dict:
    instance = db.get(ProcessInstance, task.instance_id)
    if instance is None or instance.biz_type != "leave_request":
        raise ApiError(WORKFLOW_TASK_INVALID, "流程实例不存在或类型不支持")
    leave = db.get(LeaveRequest, instance.biz_id)
    if leave is None:
        raise ApiError(RESOURCE_NOT_FOUND, "请假申请不存在")

    now = time_provider.now()
    task.action = action
    task.note = note
    task.updated_at = now
    task.completed_at = now

    if task.node_key == "manager_review":
        if leave.status != "submitted":
            raise ApiError(APPEAL_STATUS_INVALID, "请假状态不允许上级审批")
        leave.manager_note = note
        if action == "reject":
            leave.status = "rejected"
            task.status = "rejected"
            instance.status = "rejected"
            instance.current_node = None
        else:
            task.status = "completed"
            if leave.days > LEAVE_HR_REVIEW_THRESHOLD_DAYS:
                leave.status = "manager_approved"
                instance.status = "running"
                instance.current_node = "hr_review"
                hr_id = _hr_id(db)
                db.add(
                    ProcessTask(
                        instance_id=instance.id,
                        node_key="hr_review",
                        assignee_id=hr_id,
                        status="todo",
                        created_at=now,
                        updated_at=now,
                    )
                )
            else:
                leave.status = "approved"
                instance.status = "completed"
                instance.current_node = None
    elif task.node_key == "hr_review":
        if leave.status != "manager_approved":
            raise ApiError(APPEAL_STATUS_INVALID, "请假状态不允许 HR 审批")
        leave.hr_note = note
        if action == "reject":
            leave.status = "rejected"
            task.status = "rejected"
            instance.status = "rejected"
        else:
            leave.status = "approved"
            task.status = "completed"
            instance.status = "completed"
        instance.current_node = None
    else:
        raise ApiError(WORKFLOW_TASK_INVALID, "未知流程节点")

    leave.updated_at = now
    instance.updated_at = now
    db.commit()
    db.refresh(leave)
    return leave_payload(db, leave)


def return_leave_task(db: Session, user: User, task: ProcessTask, note: str | None) -> dict:
    instance = db.get(ProcessInstance, task.instance_id)
    if instance is None or instance.biz_type != "leave_request":
        raise ApiError(WORKFLOW_TASK_INVALID, "流程实例不存在或类型不支持")
    leave = db.get(LeaveRequest, instance.biz_id)
    if leave is None:
        raise ApiError(RESOURCE_NOT_FOUND, "请假申请不存在")
    if task.node_key == "manager_review" and leave.status != "submitted":
        raise ApiError(LEAVE_RETURN_FORBIDDEN, "当前状态不允许上级退回")
    if task.node_key == "hr_review" and leave.status != "manager_approved":
        raise ApiError(LEAVE_RETURN_FORBIDDEN, "当前状态不允许 HR 退回")
    if task.node_key not in {"manager_review", "hr_review"}:
        raise ApiError(LEAVE_RETURN_FORBIDDEN, "当前节点不允许退回")

    now = time_provider.now()
    task.status = "returned"
    task.action = "return"
    task.note = note
    task.updated_at = now
    task.completed_at = now
    leave.status = "returned"
    leave.return_reason = note
    leave.updated_at = now
    instance.status = "returned"
    instance.current_node = "returned"
    instance.updated_at = now
    db.commit()
    db.refresh(leave)
    return leave_payload(db, leave)


def resubmit_leave_instance(
    db: Session,
    user: User,
    instance_id: int,
    body: LeaveResubmitRequest,
) -> dict:
    instance = db.get(ProcessInstance, instance_id)
    if instance is None or instance.biz_type != "leave_request" or instance.applicant_id != user.id:
        raise ApiError(RESOURCE_NOT_FOUND, "流程实例不存在或无权限访问")
    leave = db.get(LeaveRequest, instance.biz_id)
    if leave is None:
        raise ApiError(RESOURCE_NOT_FOUND, "请假申请不存在")
    if instance.status != "returned" or leave.status != "returned":
        raise ApiError(LEAVE_RESUBMIT_FORBIDDEN, "当前状态不允许重新提交")

    leave_type, start_date, end_date, days = _validated_leave_values(body)
    attachment_files = _validated_attachment_files(db, user, body.attachment_file_ids)
    manager_id = _manager_id(db, user)
    now = time_provider.now()
    leave.leave_type = leave_type
    leave.start_date = start_date
    leave.end_date = end_date
    leave.days = days
    leave.reason = body.reason.strip()
    leave.status = "submitted"
    leave.return_reason = None
    leave.manager_note = None
    leave.hr_note = None
    leave.updated_at = now
    _replace_leave_attachments(db, leave.id, attachment_files, now)

    instance.title = f"请假申请：{LEAVE_TYPE_LABELS[leave.leave_type]} {leave.start_date} 至 {leave.end_date}"
    instance.status = "running"
    instance.current_node = "manager_review"
    instance.updated_at = now
    db.add(
        ProcessTask(
            instance_id=instance.id,
            node_key="manager_review",
            assignee_id=manager_id,
            status="todo",
            created_at=now,
            updated_at=now,
        )
    )
    db.commit()
    db.refresh(leave)
    return leave_payload(db, leave)


def latest_leave(db: Session, username: str | None = None, user_id: int | None = None) -> dict:
    user: User | None = None
    if username:
        user = db.scalar(select(User).where(User.username == username))
    elif user_id is not None:
        user = db.scalar(select(User).where(User.id == user_id))
    if (username or user_id is not None) and user is None:
        return {"query": {"username": username, "user_id": user_id}, "user": None, "leave": None}
    stmt = select(LeaveRequest)
    if user is not None:
        stmt = stmt.where(LeaveRequest.user_id == user.id)
    leave = db.scalar(stmt.order_by(LeaveRequest.updated_at.desc(), LeaveRequest.id.desc()))
    if leave is not None and user is None:
        user = db.get(User, leave.user_id)
    return {
        "query": {"username": username, "user_id": user_id},
        "user": _user_payload(user),
        "leave": leave_payload(db, leave) if leave else None,
    }


def available_actions(db: Session, instance: ProcessInstance, user: User) -> list[dict]:
    if instance.biz_type != "leave_request":
        return []
    leave = db.get(LeaveRequest, instance.biz_id)
    if leave is None:
        return []
    actions: list[dict] = []
    current_task = db.scalar(
        select(ProcessTask)
        .where(ProcessTask.instance_id == instance.id)
        .where(ProcessTask.status == "todo")
        .order_by(ProcessTask.id.desc())
    )
    if instance.applicant_id == user.id:
        if leave.status in {"submitted", "manager_approved"}:
            actions.append(_action("cancel", "取消申请", f"/api/leave/requests/{leave.id}/cancel"))
        elif leave.status == "returned":
            actions.append(_action("resubmit", "修改并重新提交", f"/api/workflow/instances/{instance.id}/resubmit"))
            actions.append(_action("cancel", "取消申请", f"/api/leave/requests/{leave.id}/cancel"))
    if current_task is not None and current_task.assignee_id == user.id and current_task.status == "todo":
        actions.extend(
            [
                _action("approve", "通过", f"/api/workflow/tasks/{current_task.id}/approve", task_id=current_task.id),
                _action("reject", "驳回", f"/api/workflow/tasks/{current_task.id}/reject", task_id=current_task.id),
                _action("return", "退回修改", f"/api/workflow/tasks/{current_task.id}/return", task_id=current_task.id),
            ]
        )
    return actions


def leave_payload(db: Session, leave: LeaveRequest) -> dict:
    user = db.get(User, leave.user_id)
    return {
        "id": leave.id,
        "user_id": leave.user_id,
        "username": user.username if user else "",
        "applicant_name": user.name if user else "",
        "process_instance_id": leave.process_instance_id,
        "leave_type": leave.leave_type,
        "leave_type_label": LEAVE_TYPE_LABELS.get(leave.leave_type, leave.leave_type),
        "start_date": leave.start_date,
        "end_date": leave.end_date,
        "days": leave.days,
        "reason": leave.reason,
        "status": leave.status,
        "status_label": leave_status_label(leave.status),
        "manager_note": leave.manager_note,
        "hr_note": leave.hr_note,
        "return_reason": leave.return_reason,
        "attachments": leave_attachments_payload(db, leave.id),
        "created_at": time_provider.fmt(leave.created_at),
        "updated_at": time_provider.fmt(leave.updated_at),
    }


def leave_attachments_payload(db: Session, leave_id: int) -> list[dict]:
    rows = db.execute(
        select(LeaveAttachment, UploadedFile)
        .join(UploadedFile, UploadedFile.file_id == LeaveAttachment.file_id)
        .where(LeaveAttachment.leave_id == leave_id)
        .order_by(LeaveAttachment.sort_order.asc(), LeaveAttachment.id.asc())
    ).all()
    return [
        {
            **file_service.uploaded_file_to_dict(uploaded),
            "attachment_id": attachment.id,
            "leave_id": attachment.leave_id,
        }
        for attachment, uploaded in rows
    ]


def leave_status_label(status: str | None) -> str:
    return {
        "submitted": "待上级审批",
        "manager_approved": "待 HR 审批",
        "returned": "已退回",
        "approved": "已通过",
        "rejected": "已驳回",
        "cancelled": "已取消",
    }.get(status or "", status or "未知")


def _validated_leave_values(body: LeaveCreateRequest) -> tuple[str, str, str, float]:
    if body.leave_type not in LEAVE_TYPE_LABELS:
        raise ApiError(LEAVE_TYPE_INVALID, "请假类型不合法")
    try:
        start = datetime.strptime(body.start_date, "%Y-%m-%d").date()
        end = datetime.strptime(body.end_date, "%Y-%m-%d").date()
    except ValueError:
        raise ApiError(LEAVE_DATE_INVALID, "请假日期不合法") from None
    if end < start:
        raise ApiError(LEAVE_DATE_INVALID, "结束日期不能早于开始日期")
    days = float((end - start).days + 1)
    if days <= 0:
        raise ApiError(LEAVE_DAYS_INVALID, "请假天数不合法")
    return body.leave_type, body.start_date, body.end_date, days


def _validated_attachment_files(db: Session, user: User, file_ids: list[str] | None) -> list[UploadedFile]:
    normalized: list[str] = []
    for file_id in file_ids or []:
        value = (file_id or "").strip()
        if value and value not in normalized:
            normalized.append(value)
    if len(normalized) > 10:
        raise ApiError(FILE_UPLOAD_INVALID, "请假附件最多 10 个")
    files: list[UploadedFile] = []
    for file_id in normalized:
        files.append(file_service.get_uploaded_file(db, file_id, user=user, usage="leave_attachment"))
    return files


def _replace_leave_attachments(
    db: Session,
    leave_id: int,
    files: list[UploadedFile],
    now: datetime,
) -> None:
    db.query(LeaveAttachment).filter(LeaveAttachment.leave_id == leave_id).delete()
    for index, uploaded in enumerate(files):
        uploaded.biz_id = f"leave:{leave_id}"
        db.add(
            LeaveAttachment(
                leave_id=leave_id,
                file_id=uploaded.file_id,
                sort_order=index,
                created_at=now,
            )
        )


def _manager_id(db: Session, user: User) -> int:
    if user.manager_id is not None:
        return user.manager_id
    manager = db.scalar(select(User).where(User.username == "manager"))
    if manager is None:
        raise ApiError(RESOURCE_NOT_FOUND, "未配置直属上级，无法提交请假")
    return manager.id


def _hr_id(db: Session) -> int:
    hr = db.scalar(select(User).where(User.is_hr == 1).order_by(User.id.asc()))
    if hr is None:
        raise ApiError(RESOURCE_NOT_FOUND, "未配置 HR 审批人")
    return hr.id


def _action(action: str, label: str, api: str, task_id: int | None = None) -> dict:
    payload = {"action": action, "label": label, "method": "POST", "api": api}
    if task_id is not None:
        payload["task_id"] = task_id
    return payload


def _user_payload(user: User | None) -> dict | None:
    if user is None:
        return None
    return {"id": user.id, "username": user.username, "name": user.name}
