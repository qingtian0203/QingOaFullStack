from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.core import time_provider
from backend.core.response import ok
from backend.db.database import get_db
from backend.db.models import Menu, Notice, User
from backend.dependencies import get_current_user

router = APIRouter(prefix="/api/home", tags=["home"])


@router.get("/menu")
def menu(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.scalars(
        select(Menu).where(Menu.section == "home").order_by(Menu.sort_order.asc(), Menu.id.asc())
    ).all()
    return ok({"menus": [_menu_item(row) for row in rows]})


@router.get("/notices")
def notices(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
):
    total = db.scalar(select(func.count(Notice.id))) or 0
    rows = db.scalars(
        select(Notice)
        .order_by(Notice.created_at.desc(), Notice.id.desc())
        .offset((page - 1) * size)
        .limit(size)
    ).all()
    return ok(
        {
            "total": total,
            "page": page,
            "size": size,
            "list": [
                {
                    "id": row.id,
                    "title": row.title,
                    "summary": row.summary,
                    "created_at": time_provider.fmt(row.created_at),
                    "is_read": False,
                }
                for row in rows
            ],
        }
    )


def _menu_item(row: Menu) -> dict:
    return {
        "id": row.id,
        "name": row.name,
        "icon": row.icon,
        "action": row.action,
        "target": row.target,
        "enabled": bool(row.enabled),
        "disabled_reason": row.disabled_reason,
    }
