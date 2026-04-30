from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ClockInRequest(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    device_id: str | None = None


class ClockRequest(ClockInRequest):
    punch_type: Literal["clock_in", "clock_out"] = "clock_in"
