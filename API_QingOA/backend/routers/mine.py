from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.core.response import ok
from backend.db.database import get_db
from backend.db.models import Menu, User
from backend.dependencies import get_current_user
from backend.routers.home import _menu_item

router = APIRouter(prefix="/api/mine", tags=["mine"])


@router.get("/menu")
def menu(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.scalars(
        select(Menu).where(Menu.section == "mine").order_by(Menu.sort_order.asc(), Menu.id.asc())
    ).all()
    return ok({"menus": [_menu_item(row) for row in rows]})
