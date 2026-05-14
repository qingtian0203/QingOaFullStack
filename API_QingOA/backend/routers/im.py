from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.core.response import ok
from backend.db.database import get_db
from backend.db.models import User
from backend.dependencies import get_current_user
from backend.schemas.im import AddFriendRequest, MarkReadRequest, SendMessageRequest, SingleConversationRequest
from backend.services import im_service

router = APIRouter(prefix="/api/im", tags=["im"])


@router.get("/users/search")
def search_users(
    q: str | None = Query(None),
    limit: int = Query(20, ge=1, le=50),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ok({"list": im_service.search_users(db, user, q=q, limit=limit)})


@router.get("/friends")
def friends(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return ok({"list": im_service.list_friends(db, user)})


@router.post("/friends")
def add_friend(
    body: AddFriendRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ok(im_service.add_friend(db, user, body.friend_user_id), msg="好友已添加")


@router.get("/conversations")
def conversations(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return ok({"list": im_service.list_conversations(db, user)})


@router.post("/conversations/single")
def single_conversation(
    body: SingleConversationRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ok(im_service.get_or_create_single_conversation(db, user, body.peer_user_id), msg="会话已创建")


@router.get("/conversations/{conversation_id}/messages")
def messages(
    conversation_id: int,
    before: int | None = Query(None),
    limit: int = Query(30, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ok({"list": im_service.list_messages(db, user, conversation_id, before=before, limit=limit)})


@router.post("/conversations/{conversation_id}/messages")
def send_message(
    conversation_id: int,
    body: SendMessageRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ok(
        im_service.send_message(
            db,
            user,
            conversation_id,
            message_type=body.message_type,
            content=body.content,
            file_id=body.file_id,
        ),
        msg="消息已发送",
    )


@router.post("/conversations/{conversation_id}/read")
def mark_read(
    conversation_id: int,
    body: MarkReadRequest | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    body = body or MarkReadRequest()
    return ok(im_service.mark_read(db, user, conversation_id, body.last_read_message_id), msg="已读状态已更新")
