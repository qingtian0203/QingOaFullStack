from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.db.models import ImConversationMember, ImMessage, ProcessInstance, ProcessTask, User


def badge_summary(db: Session, user: User) -> dict:
    todo = _workflow_task_count(db, user.id)
    urged = _workflow_task_count(db, user.id, urged=True)
    returned = _workflow_instance_count(db, user.id, "returned")
    return {
        "im": {
            "unread_total": _im_unread_total(db, user.id),
        },
        "workflow": {
            "todo": todo,
            "urged": urged,
            "processing": _workflow_instance_count(db, user.id, "running"),
            "returned": returned,
            "actionable_total": todo + returned,
        },
        "mine": {
            "punch_appeal_review": _punch_appeal_review_count(db, user.id),
        },
    }


def _im_unread_total(db: Session, user_id: int) -> int:
    unread_per_conversation = (
        select(func.count(ImMessage.id).label("cnt"))
        .select_from(ImMessage)
        .join(ImConversationMember, ImConversationMember.conversation_id == ImMessage.conversation_id)
        .where(ImConversationMember.user_id == user_id)
        .where(ImMessage.sender_id != user_id)
        .where(
            (ImConversationMember.last_read_message_id.is_(None))
            | (ImMessage.id > ImConversationMember.last_read_message_id)
        )
        .group_by(ImMessage.conversation_id)
        .subquery()
    )
    value = db.scalar(select(func.coalesce(func.sum(unread_per_conversation.c.cnt), 0)))
    return int(value or 0)


def _workflow_task_count(db: Session, user_id: int, urged: bool = False) -> int:
    stmt = (
        select(func.count(ProcessTask.id))
        .where(ProcessTask.assignee_id == user_id)
        .where(ProcessTask.status == "todo")
    )
    if urged:
        stmt = stmt.where(ProcessTask.urged == 1)
    return int(db.scalar(stmt) or 0)


def _workflow_instance_count(db: Session, user_id: int, status: str) -> int:
    return int(
        db.scalar(
            select(func.count(ProcessInstance.id))
            .where(ProcessInstance.applicant_id == user_id)
            .where(ProcessInstance.status == status)
        )
        or 0
    )


def _punch_appeal_review_count(db: Session, user_id: int) -> int:
    return int(
        db.scalar(
            select(func.count(ProcessTask.id))
            .join(ProcessInstance, ProcessTask.instance_id == ProcessInstance.id)
            .where(ProcessTask.assignee_id == user_id)
            .where(ProcessTask.status == "todo")
            .where(ProcessInstance.biz_type == "punch_appeal")
        )
        or 0
    )
