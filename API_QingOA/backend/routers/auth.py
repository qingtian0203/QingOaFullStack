from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.core.response import ok
from backend.db.database import get_db
from backend.db.models import User
from backend.dependencies import get_current_user
from backend.schemas.auth import LoginRequest
from backend.services import auth_service

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login")
def login(body: LoginRequest, db: Session = Depends(get_db)):
    return ok(auth_service.login(db, body.username, body.password))


@router.post("/logout")
def logout(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    auth_service.logout(db, user)
    return ok(None)


@router.get("/user-info")
def user_info(user: User = Depends(get_current_user)):
    return ok(auth_service.public_user(user))

