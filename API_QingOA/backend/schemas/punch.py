from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ClockInRequest(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    device_id: str | None = None


class ClockRequest(ClockInRequest):
    punch_type: Literal["clock_in", "clock_out"] = "clock_in"


class PunchAppealCreateRequest(BaseModel):
    punch_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    punch_type: Literal["clock_in", "clock_out"]
    reason: str = Field(min_length=2, max_length=200)
    expect_time: str | None = Field(default=None, pattern=r"^\d{2}:\d{2}:\d{2}$")


class PunchAppealReviewRequest(BaseModel):
    action: Literal["approve", "reject"]
    note: str | None = Field(default=None, max_length=200)
