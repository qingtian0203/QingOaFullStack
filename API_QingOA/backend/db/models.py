from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    password: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    dept: Mapped[str] = mapped_column(String, default="技术部")
    role: Mapped[str] = mapped_column(String, default="员工")
    token: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    token_expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    has_punch_permission: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    punch_records: Mapped[list["PunchRecord"]] = relationship(back_populates="user")
    okrs: Mapped[list["Okr"]] = relationship(back_populates="user")


class PunchPoint(Base):
    __tablename__ = "punch_points"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lng: Mapped[float] = mapped_column(Float, nullable=False)
    radius: Mapped[int] = mapped_column(Integer, default=500)
    is_active: Mapped[int] = mapped_column(Integer, default=1)

    punch_records: Mapped[list["PunchRecord"]] = relationship(back_populates="punch_point")


class PunchRecord(Base):
    __tablename__ = "punch_records"
    __table_args__ = (UniqueConstraint("user_id", "punch_date", "punch_type", name="uq_punch_user_date_type"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    punch_point_id: Mapped[int] = mapped_column(ForeignKey("punch_points.id"), nullable=False)
    punch_type: Mapped[str] = mapped_column(String, default="clock_in", nullable=False)
    punch_date: Mapped[str] = mapped_column(String, default="", nullable=False, index=True)
    punch_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lng: Mapped[float] = mapped_column(Float, nullable=False)
    distance: Mapped[int] = mapped_column(Integer)
    device_id: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    user: Mapped[User] = relationship(back_populates="punch_records")
    punch_point: Mapped[PunchPoint] = relationship(back_populates="punch_records")


class Notice(Base):
    __tablename__ = "notices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class Menu(Base):
    __tablename__ = "menus"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    icon: Mapped[str | None] = mapped_column(String, nullable=True)
    action: Mapped[str] = mapped_column(String, default="native")
    target: Mapped[str | None] = mapped_column(String, nullable=True)
    section: Mapped[str] = mapped_column(String, default="home", nullable=False, index=True)
    enabled: Mapped[int] = mapped_column(Integer, default=1)
    disabled_reason: Mapped[str | None] = mapped_column(String, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class Okr(Base):
    __tablename__ = "okrs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    period: Mapped[str] = mapped_column(String, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String, default="active", nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    user: Mapped[User] = relationship(back_populates="okrs")
    key_results: Mapped[list["KeyResult"]] = relationship(
        back_populates="okr",
        cascade="all, delete-orphan",
        order_by="KeyResult.id",
    )


class KeyResult(Base):
    __tablename__ = "key_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    okr_id: Mapped[int] = mapped_column(ForeignKey("okrs.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    target_value: Mapped[float] = mapped_column(Float, nullable=False)
    current_value: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    unit: Mapped[str] = mapped_column(String, default="%", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    okr: Mapped[Okr] = relationship(back_populates="key_results")
