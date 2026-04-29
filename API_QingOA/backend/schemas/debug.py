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

