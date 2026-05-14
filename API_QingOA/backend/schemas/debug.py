from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ScenarioRequest(BaseModel):
    method: str = "POST"
    path: str = Field(min_length=1)
    response: dict[str, Any]
    times: int = 1
    user_id: int | None = None
    delay_ms: int = Field(default=0, ge=0)
    http_status: int = Field(default=200, ge=100, le=599)


class FreezeTimeRequest(BaseModel):
    datetime: str = Field(pattern=r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")


class ResetTodayPunchRequest(BaseModel):
    username: str | None = None
    user_id: int | None = None
    punch_date: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")


class RecalculateAttendanceRequest(BaseModel):
    username: str
    month: str = Field(pattern=r"^\d{4}-\d{2}$")


class ResetNoticeReadRequest(BaseModel):
    username: str | None = None
    user_id: int | None = None
    notice_id: int | None = None


class ResetOkrRequest(BaseModel):
    usernames: list[str] | None = None
    user_ids: list[int] | None = None


class ResetProfileRequest(BaseModel):
    username: str | None = None
    user_id: int | None = None
    avatar_url: str = ""


class ResetImRequest(BaseModel):
    usernames: list[str] | None = None
    user_ids: list[int] | None = None
