from __future__ import annotations

import mimetypes
import re
import uuid
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from backend.core.config import MAX_UPLOAD_SIZE_BYTES, UPLOAD_DIR
from backend.core.errors import (
    FILE_UPLOAD_INVALID,
    FILE_UPLOAD_NOT_FOUND,
    FILE_UPLOAD_TOO_LARGE,
    ApiError,
)
from backend.db.models import UploadedFile, User


ALLOWED_USAGES = {"avatar", "leave_attachment", "im_image"}
AVATAR_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
ATTACHMENT_EXTENSIONS = AVATAR_EXTENSIONS | {".pdf", ".txt", ".doc", ".docx", ".xls", ".xlsx"}


def save_upload(
    db: Session,
    *,
    user: User,
    usage: str,
    filename: str,
    content_type: str | None,
    content: bytes,
    biz_id: str | None = None,
) -> UploadedFile:
    normalized_usage = (usage or "").strip()
    if normalized_usage not in ALLOWED_USAGES:
        raise ApiError(FILE_UPLOAD_INVALID, "不支持的上传用途")
    if not filename or not content:
        raise ApiError(FILE_UPLOAD_INVALID, "上传文件不能为空")
    if len(content) > MAX_UPLOAD_SIZE_BYTES:
        limit_mb = MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)
        raise ApiError(FILE_UPLOAD_TOO_LARGE, f"上传文件不能超过 {limit_mb}MB")

    safe_filename = _safe_filename(filename)
    suffix = Path(safe_filename).suffix.lower()
    mime_type = (content_type or mimetypes.guess_type(safe_filename)[0] or "application/octet-stream").lower()
    _validate_file_type(normalized_usage, suffix, mime_type)

    file_id = f"file_{datetime.now():%Y%m%d%H%M%S}_{uuid.uuid4().hex[:8]}"
    storage_dir = UPLOAD_DIR / normalized_usage
    storage_dir.mkdir(parents=True, exist_ok=True)
    storage_name = f"{file_id}{suffix or '.bin'}"
    storage_path = storage_dir / storage_name
    storage_path.write_bytes(content)

    row = UploadedFile(
        file_id=file_id,
        usage=normalized_usage,
        filename=safe_filename,
        storage_path=str(storage_path),
        url=f"/static/uploads/{normalized_usage}/{storage_name}",
        size=len(content),
        mime_type=mime_type,
        uploaded_by=user.id,
        biz_id=(biz_id or "").strip() or None,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def get_uploaded_file(db: Session, file_id: str, *, user: User | None = None, usage: str | None = None) -> UploadedFile:
    row = db.query(UploadedFile).filter(UploadedFile.file_id == file_id).first()
    if not row:
        raise ApiError(FILE_UPLOAD_NOT_FOUND, "上传文件不存在")
    if usage and row.usage != usage:
        raise ApiError(FILE_UPLOAD_INVALID, "上传文件用途不匹配")
    if user is not None and row.uploaded_by != user.id:
        raise ApiError(FILE_UPLOAD_NOT_FOUND, "上传文件不存在")
    return row


def uploaded_file_to_dict(row: UploadedFile) -> dict:
    return {
        "file_id": row.file_id,
        "url": row.url,
        "filename": row.filename,
        "size": row.size,
        "mime_type": row.mime_type,
        "usage": row.usage,
    }


def _validate_file_type(usage: str, suffix: str, mime_type: str) -> None:
    if usage == "avatar":
        if suffix not in AVATAR_EXTENSIONS or not mime_type.startswith("image/"):
            raise ApiError(FILE_UPLOAD_INVALID, "头像文件必须是 png、jpg、jpeg、webp 或 gif 图片")
        return
    if usage == "im_image":
        if suffix not in AVATAR_EXTENSIONS or not mime_type.startswith("image/"):
            raise ApiError(FILE_UPLOAD_INVALID, "IM 图片必须是 png、jpg、jpeg、webp 或 gif 图片")
        return
    if suffix not in ATTACHMENT_EXTENSIONS:
        raise ApiError(FILE_UPLOAD_INVALID, "附件类型暂不支持")


def _safe_filename(filename: str) -> str:
    name = Path(filename).name.strip() or "upload"
    return re.sub(r"[^A-Za-z0-9._\-\u4e00-\u9fff]", "_", name)[:120]
