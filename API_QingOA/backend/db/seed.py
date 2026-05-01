from __future__ import annotations

from datetime import datetime

from sqlalchemy import delete, func, select, text
from sqlalchemy.orm import Session

from backend.core.security import hash_password
from .models import KeyResult, Menu, Notice, Okr, PunchPoint, PunchRecord, User


def reset_database(db: Session) -> None:
    db.execute(delete(KeyResult))
    db.execute(delete(Okr))
    db.execute(delete(PunchRecord))
    db.execute(delete(Menu))
    db.execute(delete(Notice))
    db.execute(delete(PunchPoint))
    db.execute(delete(User))
    has_sequence = db.execute(
        text("SELECT name FROM sqlite_master WHERE type='table' AND name='sqlite_sequence'")
    ).scalar()
    if has_sequence:
        db.execute(
            text(
                "DELETE FROM sqlite_sequence "
                "WHERE name IN ('users','punch_points','punch_records','notices','menus','okrs','key_results')"
            )
        )
    db.commit()

    password = hash_password("123456")
    users = [
        User(username="konglingjia", password=password, name="晴天", dept="技术部", role="员工", has_punch_permission=1),
        User(username="nopunch", password=password, name="李四", dept="行政部", role="员工", has_punch_permission=0),
        User(username="expired", password=password, name="王五", dept="测试部", role="员工", has_punch_permission=1),
        User(username="faraday", password=password, name="法拉第", dept="外勤部", role="员工", has_punch_permission=1),
    ]
    db.add_all(users)

    db.add(PunchPoint(name="晴天打卡点", lat=39.811774, lng=116.295234, radius=500, is_active=1))

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
            section="home",
            enabled=1,
            disabled_reason=None,
            sort_order=1,
        ),
        Menu(
            name="审批流",
            icon="ic_workflow",
            action="native",
            target="WorkflowActivity",
            section="home",
            enabled=0,
            disabled_reason="功能开发中",
            sort_order=2,
        ),
        Menu(
            name="通知公告",
            icon="ic_notice",
            action="native",
            target="NoticeListActivity",
            section="home",
            enabled=0,
            disabled_reason="功能开发中",
            sort_order=3,
        ),
        Menu(
            name="我的打卡记录",
            icon="ic_punch_record",
            action="native",
            target="PunchRecordListActivity",
            section="mine",
            enabled=1,
            disabled_reason=None,
            sort_order=1,
        ),
    ]
    db.add_all(menus)
    db.flush()
    seed_okrs(db, users)
    db.commit()


def seed_if_empty(db: Session) -> None:
    count = db.scalar(select(func.count(User.id))) or 0
    if count == 0:
        reset_database(db)
    else:
        ensure_v15_static_data(db)


def ensure_v15_static_data(db: Session) -> None:
    menu_specs = [
        {
            "name": "考勤打卡",
            "icon": "ic_punch",
            "action": "native",
            "target": "PunchCardActivity",
            "section": "home",
            "enabled": 1,
            "disabled_reason": None,
            "sort_order": 1,
        },
        {
            "name": "审批流",
            "icon": "ic_workflow",
            "action": "native",
            "target": "WorkflowActivity",
            "section": "home",
            "enabled": 0,
            "disabled_reason": "功能开发中",
            "sort_order": 2,
        },
        {
            "name": "通知公告",
            "icon": "ic_notice",
            "action": "native",
            "target": "NoticeListActivity",
            "section": "home",
            "enabled": 0,
            "disabled_reason": "功能开发中",
            "sort_order": 3,
        },
        {
            "name": "我的打卡记录",
            "icon": "ic_punch_record",
            "action": "native",
            "target": "PunchRecordListActivity",
            "section": "mine",
            "enabled": 1,
            "disabled_reason": None,
            "sort_order": 1,
        },
    ]
    db.execute(delete(Menu).where(Menu.section == "mine").where(Menu.target == "OkrListActivity"))
    for spec in menu_specs:
        row = db.scalar(select(Menu).where(Menu.name == spec["name"]).where(Menu.section == spec["section"]))
        if row is None:
            row = Menu()
            db.add(row)
        for key, value in spec.items():
            setattr(row, key, value)
    users = db.scalars(select(User).order_by(User.id.asc())).all()
    if users and (db.scalar(select(func.count(Okr.id))) or 0) == 0:
        seed_okrs(db, users)
    db.commit()


def seed_okrs(db: Session, users: list[User]) -> None:
    user_map = {user.username: user for user in users}
    owner = user_map.get("konglingjia")
    faraday = user_map.get("faraday")
    if owner is not None:
        tech_okr = Okr(
            user_id=owner.id,
            title="Q2 技术能力提升",
            description="通过系统性学习和实战交付提升移动 OA 全栈能力。",
            period="2026-Q2",
            status="active",
            created_at=datetime(2026, 4, 1, 9, 0, 0),
            updated_at=datetime(2026, 4, 1, 9, 0, 0),
        )
        tech_okr.key_results = [
            KeyResult(title="完成 3 个项目后端", target_value=3, current_value=1, unit="个"),
            KeyResult(title="沉淀 5 条自动化测试链路", target_value=5, current_value=2, unit="条"),
            KeyResult(title="学习 FastAPI 最佳实践", target_value=100, current_value=60, unit="%"),
        ]
        delivery_okr = Okr(
            user_id=owner.id,
            title="Q2 自动化测试闭环",
            description="让 App、接口和调试工具形成可重复验证的演示闭环。",
            period="2026-Q2",
            status="active",
            created_at=datetime(2026, 4, 2, 9, 0, 0),
            updated_at=datetime(2026, 4, 2, 9, 0, 0),
        )
        delivery_okr.key_results = [
            KeyResult(title="覆盖登录与打卡核心用例", target_value=4, current_value=3, unit="个"),
            KeyResult(title="补齐调试接口日志", target_value=100, current_value=100, unit="%"),
        ]
        db.add_all([tech_okr, delivery_okr])
    if faraday is not None:
        faraday_okr = Okr(
            user_id=faraday.id,
            title="外勤坐标测试",
            description="用于验证 OKR 权限隔离，konglingjia 不应访问。",
            period="2026-Q2",
            status="active",
            created_at=datetime(2026, 4, 3, 9, 0, 0),
            updated_at=datetime(2026, 4, 3, 9, 0, 0),
        )
        faraday_okr.key_results = [
            KeyResult(title="完成远距离打卡验证", target_value=1, current_value=0, unit="次"),
        ]
        db.add(faraday_okr)
