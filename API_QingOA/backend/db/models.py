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
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    phone: Mapped[str | None] = mapped_column(String, nullable=True)
    email: Mapped[str | None] = mapped_column(String, nullable=True)
    office_location: Mapped[str | None] = mapped_column(String, nullable=True)
    manager_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    is_hr: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

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
    status: Mapped[str] = mapped_column(String, default="normal", nullable=False, index=True)
    source: Mapped[str] = mapped_column(String, default="manual", nullable=False)
    appeal_id: Mapped[int | None] = mapped_column(ForeignKey("punch_appeals.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    user: Mapped[User] = relationship(back_populates="punch_records")
    punch_point: Mapped[PunchPoint] = relationship(back_populates="punch_records")


class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    file_id: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    usage: Mapped[str] = mapped_column(String, nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String, nullable=False)
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    size: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String, nullable=False)
    uploaded_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    biz_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class ImFriend(Base):
    __tablename__ = "im_friends"
    __table_args__ = (UniqueConstraint("user_id", "friend_user_id", name="uq_im_friend_pair"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    friend_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String, default="accepted", nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class ImConversation(Base):
    __tablename__ = "im_conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    type: Mapped[str] = mapped_column(String, default="single", nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class ImConversationMember(Base):
    __tablename__ = "im_conversation_members"
    __table_args__ = (UniqueConstraint("conversation_id", "user_id", name="uq_im_conversation_member"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("im_conversations.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    last_read_message_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class ImMessage(Base):
    __tablename__ = "im_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("im_conversations.id"), nullable=False, index=True)
    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    message_type: Mapped[str] = mapped_column(String, nullable=False, index=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_id: Mapped[str | None] = mapped_column(ForeignKey("uploaded_files.file_id"), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String, default="sent", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class Notice(Base):
    __tablename__ = "notices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class PunchAppeal(Base):
    __tablename__ = "punch_appeals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    process_instance_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    punch_date: Mapped[str] = mapped_column(String, nullable=False, index=True)
    punch_type: Mapped[str] = mapped_column(String, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    expect_time: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="submitted", nullable=False, index=True)
    manager_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    hr_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class LeaveRequest(Base):
    __tablename__ = "leave_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    process_instance_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    leave_type: Mapped[str] = mapped_column(String, nullable=False)
    start_date: Mapped[str] = mapped_column(String, nullable=False, index=True)
    end_date: Mapped[str] = mapped_column(String, nullable=False, index=True)
    days: Mapped[float] = mapped_column(Float, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String, default="submitted", nullable=False, index=True)
    manager_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    hr_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    return_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class LeaveAttachment(Base):
    __tablename__ = "leave_attachments"
    __table_args__ = (UniqueConstraint("leave_id", "file_id", name="uq_leave_attachment_file"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    leave_id: Mapped[int] = mapped_column(ForeignKey("leave_requests.id"), nullable=False, index=True)
    file_id: Mapped[str] = mapped_column(ForeignKey("uploaded_files.file_id"), nullable=False, index=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class ProcessInstance(Base):
    __tablename__ = "process_instances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    biz_type: Mapped[str] = mapped_column(String, nullable=False, index=True)
    biz_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    applicant_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String, default="running", nullable=False, index=True)
    current_node: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class ProcessTask(Base):
    __tablename__ = "process_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    instance_id: Mapped[int] = mapped_column(ForeignKey("process_instances.id"), nullable=False, index=True)
    node_key: Mapped[str] = mapped_column(String, nullable=False)
    assignee_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String, default="todo", nullable=False, index=True)
    urged: Mapped[int] = mapped_column(Integer, default=0)
    action: Mapped[str | None] = mapped_column(String, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class NoticeRead(Base):
    __tablename__ = "notice_reads"
    __table_args__ = (UniqueConstraint("notice_id", "user_id", name="uq_notice_read_user"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    notice_id: Mapped[int] = mapped_column(ForeignKey("notices.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    read_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


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
