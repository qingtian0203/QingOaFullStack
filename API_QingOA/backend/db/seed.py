from __future__ import annotations

from datetime import datetime

from sqlalchemy import delete, func, select, text
from sqlalchemy.orm import Session

from backend.core.security import hash_password
from .models import Menu, Notice, PunchPoint, PunchRecord, User


def reset_database(db: Session) -> None:
    db.execute(delete(PunchRecord))
    db.execute(delete(Menu))
    db.execute(delete(Notice))
    db.execute(delete(PunchPoint))
    db.execute(delete(User))
    has_sequence = db.execute(
        text("SELECT name FROM sqlite_master WHERE type='table' AND name='sqlite_sequence'")
    ).scalar()
    if has_sequence:
        db.execute(text("DELETE FROM sqlite_sequence WHERE name IN ('users','punch_points','punch_records','notices','menus')"))
    db.commit()

    password = hash_password("123456")
    users = [
        User(username="admin", password=password, name="张三", dept="技术部", role="员工", has_punch_permission=1),
        User(username="nopunch", password=password, name="李四", dept="行政部", role="员工", has_punch_permission=0),
        User(username="expired", password=password, name="王五", dept="测试部", role="员工", has_punch_permission=1),
        User(username="faraday", password=password, name="法拉第", dept="外勤部", role="员工", has_punch_permission=1),
    ]
    db.add_all(users)

    db.add(PunchPoint(name="总部大楼", lat=39.9042, lng=116.4074, radius=500, is_active=1))

    notices = [
        Notice(
            title="关于春节放假安排的通知",
            summary="根据国家法定节假日安排，公司春节期间放假调休。",
            content="请各部门提前安排值班与交接事项。",
            created_at=datetime(2026, 4, 1, 10, 0, 0),
        ),
        Notice(
            title="移动 OA v1.0 试运行公告",
            summary="透明 OA 演示系统进入 v1.0 联调阶段。",
            content="本公告用于首页列表展示与自动化测试识别。",
            created_at=datetime(2026, 4, 2, 10, 0, 0),
        ),
        Notice(
            title="考勤打卡测试说明",
            summary="测试期间可使用调试接口重置打卡数据。",
            content="请勿在生产环境开放 debug 接口。",
            created_at=datetime(2026, 4, 3, 10, 0, 0),
        ),
        Notice(
            title="审批流模块开发中",
            summary="审批流入口已灰显展示，后续版本开放。",
            content="v1.0 不实现审批流页面。",
            created_at=datetime(2026, 4, 4, 10, 0, 0),
        ),
        Notice(
            title="通知公告详情开发中",
            summary="v1.0 仅展示公告列表，不实现详情页。",
            content="通知详情将在后续版本开放。",
            created_at=datetime(2026, 4, 5, 10, 0, 0),
        ),
    ]
    db.add_all(notices)

    menus = [
        Menu(
            name="考勤打卡",
            icon="ic_punch",
            action="native",
            target="PunchCardActivity",
            enabled=1,
            disabled_reason=None,
            sort_order=1,
        ),
        Menu(
            name="审批流",
            icon="ic_workflow",
            action="native",
            target="WorkflowActivity",
            enabled=0,
            disabled_reason="功能开发中",
            sort_order=2,
        ),
        Menu(
            name="通知公告",
            icon="ic_notice",
            action="native",
            target="NoticeActivity",
            enabled=0,
            disabled_reason="功能开发中",
            sort_order=3,
        ),
    ]
    db.add_all(menus)
    db.commit()


def seed_if_empty(db: Session) -> None:
    count = db.scalar(select(func.count(User.id))) or 0
    if count == 0:
        reset_database(db)
