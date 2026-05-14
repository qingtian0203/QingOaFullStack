from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.core.response import ok
from backend.db.database import get_db
from backend.db.models import User
from backend.dependencies import get_current_user
from backend.schemas.leave import LeaveResubmitRequest
from backend.services import punch_service

router = APIRouter(prefix="/api/workflow", tags=["workflow"])


class WorkflowReviewRequest(BaseModel):
    note: str | None = None


@router.get("/templates")
def templates(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ok(punch_service.workflow_templates(db, user))


@router.get("/tasks")
def tasks(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    bucket: str = Query("todo"),
):
    return ok(punch_service.workflow_tasks(db, user, bucket))


@router.get("/instances")
def instances(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    bucket: str = Query("processing"),
):
    return ok(punch_service.workflow_instances(db, user, bucket))


@router.get("/instances/{instance_id}")
def instance_detail(
    instance_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ok(punch_service.workflow_instance_detail(db, user, instance_id))


@router.post("/tasks/{task_id}/approve")
def approve_task(
    task_id: int,
    body: WorkflowReviewRequest | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    note = body.note if body else None
    return ok(punch_service.review_workflow_task(db, user, task_id, "approve", note), msg="审批已通过")


@router.post("/tasks/{task_id}/reject")
def reject_task(
    task_id: int,
    body: WorkflowReviewRequest | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    note = body.note if body else None
    return ok(punch_service.review_workflow_task(db, user, task_id, "reject", note), msg="审批已驳回")


@router.post("/tasks/{task_id}/return")
def return_task(
    task_id: int,
    body: WorkflowReviewRequest | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    note = body.note if body else None
    return ok(punch_service.return_workflow_task(db, user, task_id, note), msg="已退回申请人修改")


@router.post("/instances/{instance_id}/resubmit")
def resubmit_instance(
    instance_id: int,
    body: LeaveResubmitRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ok(punch_service.resubmit_workflow_instance(db, user, instance_id, body), msg="已重新提交")


@router.post("/instances/{instance_id}/urge")
def urge_instance(
    instance_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ok(punch_service.urge_instance(db, user, instance_id), msg="已催办")
