from __future__ import annotations

from datetime import datetime

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from backend.core import time_provider
from backend.core.errors import BAD_REQUEST, FILE_UPLOAD_INVALID, RESOURCE_NOT_FOUND, ApiError
from backend.db.models import ImConversation, ImConversationMember, ImFriend, ImMessage, UploadedFile, User


def search_users(db: Session, current_user: User, q: str | None = None, limit: int = 20) -> list[dict]:
    keyword = (q or "").strip()
    stmt = select(User).where(User.id != current_user.id).order_by(User.id.asc()).limit(max(1, min(limit, 50)))
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where((User.username.like(like)) | (User.name.like(like)))
    users = list(db.scalars(stmt).all())
    friend_ids = {
        row.friend_user_id
        for row in db.scalars(select(ImFriend).where(ImFriend.user_id == current_user.id)).all()
    }
    return [_user_payload(row, is_friend=row.id in friend_ids) for row in users]


def list_friends(db: Session, current_user: User) -> list[dict]:
    rows = db.scalars(
        select(ImFriend).where(ImFriend.user_id == current_user.id).order_by(ImFriend.id.asc())
    ).all()
    friend_ids = [row.friend_user_id for row in rows]
    if not friend_ids:
        return []
    users = {
        user.id: user
        for user in db.scalars(select(User).where(User.id.in_(friend_ids)).order_by(User.id.asc())).all()
    }
    return [
        _user_payload(users[row.friend_user_id], is_friend=True, status=row.status)
        for row in rows
        if row.friend_user_id in users
    ]


def add_friend(db: Session, current_user: User, friend_user_id: int) -> dict:
    friend = _require_user(db, friend_user_id)
    if friend.id == current_user.id:
        raise ApiError(BAD_REQUEST, "不能添加自己为好友")
    _ensure_friend_pair(db, current_user.id, friend.id)
    db.commit()
    return _user_payload(friend, is_friend=True, status="accepted")


def get_or_create_single_conversation(db: Session, current_user: User, peer_user_id: int) -> dict:
    peer = _require_user(db, peer_user_id)
    if peer.id == current_user.id:
        raise ApiError(BAD_REQUEST, "不能和自己创建单聊")
    _ensure_friend_pair(db, current_user.id, peer.id)
    conversation = _find_single_conversation(db, current_user.id, peer.id)
    if conversation is None:
        now = time_provider.now()
        conversation = ImConversation(type="single", created_at=now, updated_at=now)
        db.add(conversation)
        db.flush()
        db.add_all(
            [
                ImConversationMember(conversation_id=conversation.id, user_id=current_user.id),
                ImConversationMember(conversation_id=conversation.id, user_id=peer.id),
            ]
        )
    db.commit()
    db.refresh(conversation)
    return conversation_payload(db, conversation, current_user)


def list_conversations(db: Session, current_user: User) -> list[dict]:
    conversation_ids = list(
        db.scalars(
            select(ImConversationMember.conversation_id).where(ImConversationMember.user_id == current_user.id)
        ).all()
    )
    if not conversation_ids:
        return []
    conversations = db.scalars(
        select(ImConversation)
        .where(ImConversation.id.in_(conversation_ids))
        .order_by(ImConversation.updated_at.desc(), ImConversation.id.desc())
    ).all()
    return [conversation_payload(db, row, current_user) for row in conversations]


def list_messages(db: Session, current_user: User, conversation_id: int, before: int | None = None, limit: int = 30) -> list[dict]:
    _require_member(db, conversation_id, current_user.id)
    stmt = select(ImMessage).where(ImMessage.conversation_id == conversation_id)
    if before is not None:
        stmt = stmt.where(ImMessage.id < before)
    rows = list(
        db.scalars(stmt.order_by(ImMessage.id.desc()).limit(max(1, min(limit, 100)))).all()
    )
    rows.reverse()
    return [message_payload(db, row) for row in rows]


def send_message(
    db: Session,
    current_user: User,
    conversation_id: int,
    *,
    message_type: str,
    content: str | None = None,
    file_id: str | None = None,
) -> dict:
    _require_member(db, conversation_id, current_user.id)
    conversation = _require_conversation(db, conversation_id)
    now = time_provider.now()

    if message_type == "text":
        text = (content or "").strip()
        if not text:
            raise ApiError(BAD_REQUEST, "消息内容不能为空")
        message = ImMessage(
            conversation_id=conversation_id,
            sender_id=current_user.id,
            message_type="text",
            content=text,
            file_id=None,
            created_at=now,
        )
    elif message_type == "image":
        clean_file_id = (file_id or "").strip()
        if not clean_file_id:
            raise ApiError(FILE_UPLOAD_INVALID, "图片消息必须传入 file_id")
        _require_im_image(db, clean_file_id, current_user)
        message = ImMessage(
            conversation_id=conversation_id,
            sender_id=current_user.id,
            message_type="image",
            content=None,
            file_id=clean_file_id,
            created_at=now,
        )
    else:
        raise ApiError(BAD_REQUEST, "不支持的消息类型")

    conversation.updated_at = now
    db.add(message)
    db.commit()
    db.refresh(message)
    return message_payload(db, message)


def mark_read(db: Session, current_user: User, conversation_id: int, last_read_message_id: int | None = None) -> dict:
    member = _require_member(db, conversation_id, current_user.id)
    if last_read_message_id is None:
        last_read_message_id = db.scalar(
            select(func.max(ImMessage.id)).where(ImMessage.conversation_id == conversation_id)
        )
    current_value = member.last_read_message_id or 0
    next_value = last_read_message_id or current_value
    member.last_read_message_id = max(current_value, next_value)
    db.commit()
    return {"conversation_id": conversation_id, "last_read_message_id": member.last_read_message_id}


def debug_state(db: Session, username: str | None = None) -> dict:
    user = db.scalar(select(User).where(User.username == username)) if username else None
    if username and user is None:
        return {"user": None, "friends": [], "conversations": [], "messages": []}

    friend_stmt = select(ImFriend).order_by(ImFriend.id.asc())
    member_stmt = select(ImConversationMember).order_by(ImConversationMember.id.asc())
    message_stmt = select(ImMessage).order_by(ImMessage.id.asc())
    if user is not None:
        friend_stmt = friend_stmt.where(ImFriend.user_id == user.id)
        conversation_ids = list(
            db.scalars(select(ImConversationMember.conversation_id).where(ImConversationMember.user_id == user.id)).all()
        )
        member_stmt = member_stmt.where(ImConversationMember.conversation_id.in_(conversation_ids or [-1]))
        message_stmt = message_stmt.where(ImMessage.conversation_id.in_(conversation_ids or [-1]))

    friends = db.scalars(friend_stmt).all()
    members = db.scalars(member_stmt).all()
    messages = db.scalars(message_stmt).all()
    conversation_ids = sorted({row.conversation_id for row in members})
    conversations = []
    if conversation_ids:
        conversations = [
            conversation_payload(db, row, user) if user else _debug_conversation_payload(db, row)
            for row in db.scalars(
                select(ImConversation).where(ImConversation.id.in_(conversation_ids)).order_by(ImConversation.id.asc())
            ).all()
        ]

    return {
        "user": _user_payload(user, is_friend=False) if user else None,
        "friends": [
            {
                "id": row.id,
                "user_id": row.user_id,
                "friend_user_id": row.friend_user_id,
                "status": row.status,
                "created_at": time_provider.fmt(row.created_at),
            }
            for row in friends
        ],
        "conversations": conversations,
        "members": [
            {
                "conversation_id": row.conversation_id,
                "user_id": row.user_id,
                "last_read_message_id": row.last_read_message_id,
            }
            for row in members
        ],
        "messages": [message_payload(db, row) for row in messages],
    }


def debug_reset(db: Session, usernames: list[str] | None = None, user_ids: list[int] | None = None) -> dict:
    target_user_ids = _target_user_ids(db, usernames=usernames, user_ids=user_ids)
    if usernames or user_ids:
        if not target_user_ids:
            return {"deleted_count": 0, "user_ids": [], "usernames": usernames or []}
        conversation_ids = list(
            db.scalars(
                select(ImConversationMember.conversation_id).where(ImConversationMember.user_id.in_(target_user_ids))
            ).all()
        )
        db.execute(delete(ImFriend).where((ImFriend.user_id.in_(target_user_ids)) | (ImFriend.friend_user_id.in_(target_user_ids))))
        if conversation_ids:
            db.execute(delete(ImMessage).where(ImMessage.conversation_id.in_(conversation_ids)))
            db.execute(delete(ImConversationMember).where(ImConversationMember.conversation_id.in_(conversation_ids)))
            db.execute(delete(ImConversation).where(ImConversation.id.in_(conversation_ids)))
        upload_result = db.execute(
            delete(UploadedFile)
            .where(UploadedFile.usage == "im_image")
            .where(UploadedFile.uploaded_by.in_(target_user_ids))
        )
        deleted_count = len(conversation_ids) + (upload_result.rowcount or 0)
    else:
        message_result = db.execute(delete(ImMessage))
        member_result = db.execute(delete(ImConversationMember))
        conversation_result = db.execute(delete(ImConversation))
        friend_result = db.execute(delete(ImFriend))
        upload_result = db.execute(delete(UploadedFile).where(UploadedFile.usage == "im_image"))
        deleted_count = sum(
            item or 0
            for item in (
                message_result.rowcount,
                member_result.rowcount,
                conversation_result.rowcount,
                friend_result.rowcount,
                upload_result.rowcount,
            )
        )
    db.commit()
    return {"deleted_count": deleted_count, "user_ids": target_user_ids, "usernames": usernames or []}


def conversation_payload(db: Session, conversation: ImConversation, current_user: User | None) -> dict:
    members = list(
        db.scalars(
            select(ImConversationMember)
            .where(ImConversationMember.conversation_id == conversation.id)
            .order_by(ImConversationMember.id.asc())
        ).all()
    )
    current_member = next((row for row in members if current_user is not None and row.user_id == current_user.id), None)
    peer_member = next((row for row in members if current_user is None or row.user_id != current_user.id), None)
    peer = db.scalar(select(User).where(User.id == peer_member.user_id)) if peer_member else None
    last_message = db.scalar(
        select(ImMessage)
        .where(ImMessage.conversation_id == conversation.id)
        .order_by(ImMessage.id.desc())
        .limit(1)
    )
    unread_count = 0
    if current_user is not None and current_member is not None:
        stmt = (
            select(func.count(ImMessage.id))
            .where(ImMessage.conversation_id == conversation.id)
            .where(ImMessage.sender_id != current_user.id)
        )
        if current_member.last_read_message_id is not None:
            stmt = stmt.where(ImMessage.id > current_member.last_read_message_id)
        unread_count = db.scalar(stmt) or 0
    return {
        "id": conversation.id,
        "type": conversation.type,
        "peer": _user_payload(peer, is_friend=True) if peer else None,
        "last_message": _last_message_payload(db, last_message),
        "unread_count": unread_count,
        "updated_at": time_provider.fmt(conversation.updated_at),
        "created_at": time_provider.fmt(conversation.created_at),
    }


def message_payload(db: Session, message: ImMessage) -> dict:
    file_payload = None
    if message.file_id:
        uploaded = db.scalar(select(UploadedFile).where(UploadedFile.file_id == message.file_id))
        file_payload = _file_payload(uploaded) if uploaded else None
    return {
        "id": message.id,
        "conversation_id": message.conversation_id,
        "sender_id": message.sender_id,
        "message_type": message.message_type,
        "content": message.content or "",
        "file_id": message.file_id,
        "file": file_payload,
        "status": message.status,
        "created_at": time_provider.fmt(message.created_at),
    }


def _ensure_friend_pair(db: Session, user_id: int, friend_user_id: int) -> None:
    for left, right in ((user_id, friend_user_id), (friend_user_id, user_id)):
        row = db.scalar(select(ImFriend).where(ImFriend.user_id == left, ImFriend.friend_user_id == right))
        if row is None:
            db.add(ImFriend(user_id=left, friend_user_id=right, status="accepted"))
        else:
            row.status = "accepted"
    db.flush()


def _find_single_conversation(db: Session, user_id: int, peer_user_id: int) -> ImConversation | None:
    candidate_ids = list(
        db.scalars(
            select(ImConversationMember.conversation_id).where(ImConversationMember.user_id == user_id)
        ).all()
    )
    for conversation_id in candidate_ids:
        members = set(
            db.scalars(
                select(ImConversationMember.user_id).where(ImConversationMember.conversation_id == conversation_id)
            ).all()
        )
        if members == {user_id, peer_user_id}:
            conversation = db.scalar(
                select(ImConversation).where(ImConversation.id == conversation_id, ImConversation.type == "single")
            )
            if conversation is not None:
                return conversation
    return None


def _require_user(db: Session, user_id: int) -> User:
    user = db.scalar(select(User).where(User.id == user_id))
    if user is None:
        raise ApiError(RESOURCE_NOT_FOUND, "用户不存在")
    return user


def _require_conversation(db: Session, conversation_id: int) -> ImConversation:
    conversation = db.scalar(select(ImConversation).where(ImConversation.id == conversation_id))
    if conversation is None:
        raise ApiError(RESOURCE_NOT_FOUND, "会话不存在")
    return conversation


def _require_member(db: Session, conversation_id: int, user_id: int) -> ImConversationMember:
    member = db.scalar(
        select(ImConversationMember).where(
            ImConversationMember.conversation_id == conversation_id,
            ImConversationMember.user_id == user_id,
        )
    )
    if member is None:
        raise ApiError(RESOURCE_NOT_FOUND, "会话不存在或无权访问")
    return member


def _require_im_image(db: Session, file_id: str, user: User) -> UploadedFile:
    uploaded = db.scalar(select(UploadedFile).where(UploadedFile.file_id == file_id))
    if uploaded is None or uploaded.uploaded_by != user.id:
        raise ApiError(RESOURCE_NOT_FOUND, "上传文件不存在")
    if uploaded.usage != "im_image":
        raise ApiError(FILE_UPLOAD_INVALID, "上传文件用途不匹配")
    if not uploaded.mime_type.startswith("image/"):
        raise ApiError(FILE_UPLOAD_INVALID, "图片消息文件类型无效")
    return uploaded


def _target_user_ids(db: Session, usernames: list[str] | None, user_ids: list[int] | None) -> list[int]:
    names = [item for item in (usernames or []) if item]
    ids = [item for item in (user_ids or []) if item is not None]
    if not names and not ids:
        return []
    stmt = select(User.id)
    if names and ids:
        stmt = stmt.where((User.username.in_(names)) | (User.id.in_(ids)))
    elif names:
        stmt = stmt.where(User.username.in_(names))
    else:
        stmt = stmt.where(User.id.in_(ids))
    return list(db.scalars(stmt).all())


def _user_payload(user: User | None, *, is_friend: bool, status: str = "accepted") -> dict | None:
    if user is None:
        return None
    return {
        "id": user.id,
        "user_id": user.id,
        "username": user.username,
        "name": user.name,
        "dept": user.dept,
        "role": user.role,
        "avatar_url": user.avatar_url or "",
        "is_friend": is_friend,
        "friend_status": status if is_friend else "",
    }


def _last_message_payload(db: Session, message: ImMessage | None) -> dict | None:
    if message is None:
        return None
    payload = message_payload(db, message)
    payload["summary"] = message.content if message.message_type == "text" else "[图片]"
    return payload


def _file_payload(uploaded: UploadedFile) -> dict:
    return {
        "file_id": uploaded.file_id,
        "url": uploaded.url,
        "filename": uploaded.filename,
        "size": uploaded.size,
        "mime_type": uploaded.mime_type,
        "usage": uploaded.usage,
    }


def _debug_conversation_payload(db: Session, conversation: ImConversation) -> dict:
    payload = conversation_payload(db, conversation, None)
    payload["member_user_ids"] = list(
        db.scalars(
            select(ImConversationMember.user_id)
            .where(ImConversationMember.conversation_id == conversation.id)
            .order_by(ImConversationMember.user_id.asc())
        ).all()
    )
    return payload
