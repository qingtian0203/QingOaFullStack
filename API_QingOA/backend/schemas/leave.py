from __future__ import annotations

from pydantic import BaseModel, Field


class LeaveCreateRequest(BaseModel):
    leave_type: str = Field(min_length=1, max_length=20)
    start_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    end_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    reason: str = Field(min_length=2, max_length=300)
    attachment_file_ids: list[str] = Field(default_factory=list, max_length=10)


class LeaveResubmitRequest(LeaveCreateRequest):
    pass
