from __future__ import annotations

from pydantic import BaseModel


class UploadedFileOut(BaseModel):
    file_id: str
    url: str
    filename: str
    size: int
    mime_type: str
    usage: str
