from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from backend.core.response import ok
from backend.db.database import get_db
from backend.db.models import User
from backend.dependencies import get_current_user
from backend.services import file_service

router = APIRouter(prefix="/api/files", tags=["files"])


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    usage: str = Form(...),
    biz_id: str | None = Form(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    content = await file.read()
    uploaded = file_service.save_upload(
        db,
        user=user,
        usage=usage,
        filename=file.filename or "upload",
        content_type=file.content_type,
        content=content,
        biz_id=biz_id,
    )
    return ok(file_service.uploaded_file_to_dict(uploaded), msg="文件上传成功")
