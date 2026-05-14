from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.core.response import ok
from backend.db.database import get_db
from backend.db.models import User
from backend.dependencies import get_current_user
from backend.services import badge_service

router = APIRouter(prefix="/api/badges", tags=["badges"])


@router.get("/summary")
def summary(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return ok(badge_service.badge_summary(db, user))
