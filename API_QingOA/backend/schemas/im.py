from __future__ import annotations

from pydantic import BaseModel, Field


class AddFriendRequest(BaseModel):
    friend_user_id: int


class SingleConversationRequest(BaseModel):
    peer_user_id: int


class SendMessageRequest(BaseModel):
    message_type: str = Field(pattern="^(text|image)$")
    content: str | None = None
    file_id: str | None = None


class MarkReadRequest(BaseModel):
    last_read_message_id: int | None = None
