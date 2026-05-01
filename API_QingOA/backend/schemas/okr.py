from __future__ import annotations

from pydantic import BaseModel, Field


class KeyResultCreate(BaseModel):
    title: str = Field(min_length=1)
    target_value: float = Field(gt=0)
    current_value: float = Field(default=0, ge=0)
    unit: str = Field(default="%", min_length=1)


class OkrCreateRequest(BaseModel):
    title: str = Field(min_length=1)
    description: str | None = None
    period: str = Field(min_length=1)
    key_results: list[KeyResultCreate] = Field(min_length=1)


class KrProgressUpdateRequest(BaseModel):
    current_value: float = Field(ge=0)
