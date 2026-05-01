from __future__ import annotations

from pydantic import BaseModel


class UserProfileUpdateRequest(BaseModel):
    phone: str | None = None
    email: str | None = None
    office_location: str | None = None


class UserAvatarUpdateRequest(BaseModel):
    avatar_url: str
