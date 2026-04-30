from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy import text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from backend.core.config import DATA_DIR, DATABASE_URL


DATA_DIR.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    pass


def create_tables() -> None:
    from . import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    migrate_existing_sqlite_schema()


def migrate_existing_sqlite_schema() -> None:
    if not DATABASE_URL.startswith("sqlite:///"):
        return
    with engine.begin() as conn:
        punch_columns = _column_names(conn, "punch_records")
        if punch_columns:
            if "punch_type" not in punch_columns:
                conn.execute(text("ALTER TABLE punch_records ADD COLUMN punch_type TEXT NOT NULL DEFAULT 'clock_in'"))
            if "punch_date" not in punch_columns:
                conn.execute(text("ALTER TABLE punch_records ADD COLUMN punch_date TEXT NOT NULL DEFAULT ''"))
            conn.execute(
                text(
                    "UPDATE punch_records "
                    "SET punch_date = substr(CAST(punch_time AS TEXT), 1, 10) "
                    "WHERE punch_date IS NULL OR punch_date = ''"
                )
            )

        menu_columns = _column_names(conn, "menus")
        if menu_columns and "section" not in menu_columns:
            conn.execute(text("ALTER TABLE menus ADD COLUMN section TEXT NOT NULL DEFAULT 'home'"))


def _column_names(conn, table_name: str) -> set[str]:
    rows = conn.execute(text(f"PRAGMA table_info({table_name})")).fetchall()
    return {row[1] for row in rows}


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
