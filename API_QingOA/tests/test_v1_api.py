from __future__ import annotations

import os
from pathlib import Path
from tempfile import gettempdir

TEST_DB = Path(gettempdir()) / "qing_oa_v1_test.db"
if TEST_DB.exists():
    TEST_DB.unlink()
os.environ["QINGOA_DATABASE_URL"] = f"sqlite:///{TEST_DB}"

from fastapi.testclient import TestClient

from backend.app import app


client = TestClient(app)


def reset():
    res = client.post("/debug/reset-data")
    assert res.status_code == 200
    assert res.json()["code"] == 0


def login(username="konglingjia", password="123456"):
    res = client.post("/api/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 0
    return body["data"]["token"], body["data"]


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_login_user_info_and_home_menu():
    reset()
    token, data = login()
    assert data["username"] == "konglingjia"

    res = client.get("/api/auth/user-info", headers=auth(token))
    assert res.json()["data"]["name"] == "晴天"

    res = client.get("/api/home/menu", headers=auth(token))
    body = res.json()
    assert body["code"] == 0
    menus = body["data"]["menus"]
    assert menus[0]["enabled"] is True
    assert menus[1]["target"] == "WorkflowWebActivity"
    assert menus[1]["enabled"] is True
    assert all(menu.get("target") != "PunchRecordListActivity" for menu in menus)

    res = client.get("/api/mine/menu", headers=auth(token))
    body = res.json()
    assert body["code"] == 0
    mine_menus = body["data"]["menus"]
    assert mine_menus[0]["target"] == "PunchRecordListActivity"
    targets = {menu["target"] for menu in mine_menus}
    assert {
        "PunchRecordListActivity",
        "PunchAppealActivity",
        "PunchAppealReviewActivity",
        "WorkflowWebActivity",
    }.issubset(targets)
    assert all(menu["target"] != "OkrListActivity" for menu in mine_menus)


def test_repeated_login_replaces_active_token():
    reset()
    first_token, _ = login("konglingjia")
    second_token, _ = login("konglingjia")
    assert second_token != first_token

    res = client.get("/api/auth/user-info", headers=auth(first_token))
    assert res.json()["code"] == 1002

    res = client.get("/api/auth/user-info", headers=auth(second_token))
    assert res.json()["code"] == 0


def test_success_clock_in_and_debug_state():
    reset()
    token, data = login("konglingjia")

    res = client.post(
        "/api/punch/clock",
        headers=auth(token),
        json={
            "lat": 39.811774,
            "lng": 116.295234,
            "device_id": "android_device_001",
            "punch_type": "clock_in",
        },
    )
    body = res.json()
    assert body["code"] == 0
    assert body["msg"] == "上班打卡成功"
    assert body["data"]["point_name"] == "晴天打卡点"
    assert body["data"]["updated"] is False

    status = client.get("/api/punch/today-status", headers=auth(token)).json()["data"]
    assert status["clock_in"]["done"] is True
    assert status["clock_out"]["done"] is False
    assert status["has_punched"] is True

    state = client.get("/debug/state").json()["data"]
    assert any(
        row["user_id"] == data["user_id"] and row["punch_type"] == "clock_in"
        for row in state["today_punch_records"]
    )

    latest = client.get(
        "/debug/attendance/latest?username=konglingjia&punch_type=clock_in"
    ).json()
    assert latest["code"] == 0
    assert latest["data"]["user"]["username"] == "konglingjia"
    assert latest["data"]["record"]["punch_type"] == "clock_in"
    assert latest["data"]["record"]["point_name"] == "晴天打卡点"
    assert latest["data"]["record"]["device_id"] == "android_device_001"

    logs = client.get("/debug/requests").json()["data"]["requests"]
    clock_log = next(row for row in logs if row["path"] == "/api/punch/clock")
    assert clock_log["auth_present"] is True
    assert clock_log["response_code"] == 0


def test_clock_out_updates_today_record():
    reset()
    client.post("/debug/freeze-time", json={"datetime": "2026-04-30 09:01:00"})
    token, data = login("konglingjia")

    first = client.post(
        "/api/punch/clock",
        headers=auth(token),
        json={
            "lat": 39.811774,
            "lng": 116.295234,
            "device_id": "android_device_001",
            "punch_type": "clock_in",
        },
    ).json()
    assert first["code"] == 0
    assert first["msg"] == "上班打卡成功"

    duplicate_clock_in = client.post(
        "/api/punch/clock",
        headers=auth(token),
        json={
            "lat": 39.811774,
            "lng": 116.295234,
            "device_id": "android_device_001",
            "punch_type": "clock_in",
        },
    ).json()
    assert duplicate_clock_in["code"] == 1008

    client.post("/debug/freeze-time", json={"datetime": "2026-04-30 18:22:33"})
    second = client.post(
        "/api/punch/clock",
        headers=auth(token),
        json={
            "lat": 39.811800,
            "lng": 116.295260,
            "device_id": "android_device_002",
            "punch_type": "clock_out",
        },
    ).json()
    assert second["code"] == 0
    assert second["msg"] == "下班打卡成功"
    assert second["data"]["updated"] is False
    assert second["data"]["punch_time"] == "2026-04-30 18:22:33"

    client.post("/debug/freeze-time", json={"datetime": "2026-04-30 21:15:00"})
    updated = client.post(
        "/api/punch/clock",
        headers=auth(token),
        json={
            "lat": 39.811800,
            "lng": 116.295260,
            "device_id": "android_device_003",
            "punch_type": "clock_out",
        },
    ).json()
    assert updated["code"] == 0
    assert updated["msg"] == "下班打卡时间已更新"
    assert updated["data"]["updated"] is True
    assert updated["data"]["punch_id"] == second["data"]["punch_id"]
    assert updated["data"]["punch_time"] == "2026-04-30 21:15:00"

    state = client.get("/debug/state").json()["data"]
    rows = [row for row in state["today_punch_records"] if row["user_id"] == data["user_id"]]
    assert len(rows) == 2
    assert any(row["punch_type"] == "clock_in" for row in rows)
    assert any(row["punch_type"] == "clock_out" and row["punch_time"] == "2026-04-30 21:15:00" for row in rows)

    records = client.get("/api/punch/records", headers=auth(token)).json()["data"]
    assert records["total"] == 2
    assert records["page"] == 1
    assert records["size"] == 10
    assert records["list"][0]["punch_type"] == "clock_out"
    detail = client.get(f"/api/punch/records/{updated['data']['punch_id']}", headers=auth(token)).json()
    assert detail["code"] == 0
    assert detail["data"]["device_id"] == "android_device_003"


def test_clock_out_requires_clock_in():
    reset()
    token, _ = login("konglingjia")
    res = client.post(
        "/api/punch/clock",
        headers=auth(token),
        json={
            "lat": 39.811774,
            "lng": 116.295234,
            "device_id": "android_device_001",
            "punch_type": "clock_out",
        },
    )
    assert res.json()["code"] == 1007
    assert client.get("/debug/state").json()["data"]["today_punch_records"] == []


def test_reset_today_punch_by_username():
    reset()
    token, _ = login("konglingjia")
    client.post(
        "/api/punch/clock",
        headers=auth(token),
        json={
            "lat": 39.811774,
            "lng": 116.295234,
            "device_id": "android_device_001",
            "punch_type": "clock_in",
        },
    )
    res = client.post("/debug/punch/reset-today", json={"username": "konglingjia"})
    body = res.json()
    assert body["code"] == 0
    assert body["data"]["deleted_count"] == 1
    assert client.get("/debug/state").json()["data"]["today_punch_records"] == []


def test_reset_punch_by_explicit_date():
    reset()
    token, _ = login("konglingjia")
    client.post("/debug/freeze-time", json={"datetime": "2026-05-04 09:20:00"})
    client.post(
        "/api/punch/clock",
        headers=auth(token),
        json={
            "lat": 39.811774,
            "lng": 116.295234,
            "device_id": "android_device_001",
            "punch_type": "clock_in",
        },
    )
    client.post("/debug/freeze-time", json={"datetime": "2026-05-07 09:01:00"})

    res = client.post(
        "/debug/punch/reset-today",
        json={"username": "konglingjia", "punch_date": "2026-05-04"},
    )
    body = res.json()
    assert body["code"] == 0
    assert body["data"]["deleted_count"] == 1
    latest = client.get(
        "/debug/attendance/latest?username=konglingjia&punch_type=clock_in&punch_date=2026-05-04"
    ).json()
    assert latest["data"]["record"] is None


def test_debug_fixture_resets_notice_okr_and_profile_state():
    reset()
    token, _ = login("konglingjia")

    client.post("/api/notices/1/read", headers=auth(token))
    assert client.get("/api/notices/1", headers=auth(token)).json()["data"]["is_read"] is True
    res = client.post("/debug/notices/reset-read", json={"username": "konglingjia", "notice_id": 1})
    assert res.json()["data"]["deleted_count"] == 1
    assert client.get("/api/notices/1", headers=auth(token)).json()["data"]["is_read"] is False

    original_list = client.get("/api/okr/list", headers=auth(token)).json()["data"]["list"]
    client.delete(f"/api/okr/{original_list[0]['id']}", headers=auth(token))
    assert len(client.get("/api/okr/list", headers=auth(token)).json()["data"]["list"]) == len(original_list) - 1
    res = client.post("/debug/okr/reset", json={"usernames": ["konglingjia"]})
    assert res.json()["code"] == 0
    assert len(client.get("/api/okr/list", headers=auth(token)).json()["data"]["list"]) == len(original_list)

    client.post("/api/user/avatar", headers=auth(token), json={"avatar_url": "https://example.com/avatar.png"})
    assert client.get("/api/user/profile", headers=auth(token)).json()["data"]["avatar_url"]
    res = client.post("/debug/profile/reset", json={"username": "konglingjia"})
    assert res.json()["code"] == 0
    assert client.get("/api/user/profile", headers=auth(token)).json()["data"]["avatar_url"] == ""


def test_faraday_out_of_range_no_record():
    reset()
    token, data = login("faraday")
    res = client.post(
        "/api/punch/clock",
        headers=auth(token),
        json={
            "lat": 39.8000,
            "lng": 116.2000,
            "device_id": "android_device_001",
            "punch_type": "clock_in",
        },
    )
    body = res.json()
    assert body["code"] == 1004
    assert "不在打卡范围内" in body["msg"]

    state = client.get("/debug/state").json()["data"]
    assert not any(row["user_id"] == data["user_id"] for row in state["today_punch_records"])


def test_invalid_coordinate_returns_business_error_without_data_shape():
    reset()
    token, _ = login("konglingjia")
    res = client.post(
        "/api/punch/clock",
        headers=auth(token),
        json={"lat": 100, "lng": 60, "device_id": "android_device_001", "punch_type": "clock_in"},
    )
    body = res.json()
    assert res.status_code == 200
    assert body["code"] == 1003
    assert "纬度不能大于" in body["msg"]
    assert body["data"] is None


def test_injected_token_expired_for_user_info():
    reset()
    token, data = login("konglingjia")
    res = client.post(
        "/debug/inject-scenario",
        json={
            "method": "GET",
            "path": "/api/auth/user-info",
            "response": {"code": 1002, "msg": "Token 已过期，请重新登录", "data": None},
            "times": 1,
            "user_id": data["user_id"],
        },
    )
    assert res.json()["code"] == 0

    expired = client.get("/api/auth/user-info", headers=auth(token)).json()
    assert expired["code"] == 1002

    normal = client.get("/api/auth/user-info", headers=auth(token)).json()
    assert normal["code"] == 0


def test_notice_detail():
    reset()
    token, _ = login("konglingjia")
    res = client.get("/api/notices/1", headers=auth(token))
    body = res.json()
    assert body["code"] == 0
    assert body["data"]["title"] == "关于春节放假安排的通知"
    assert "交接事项" in body["data"]["content"]
    assert body["data"]["is_read"] is False


def test_user_profile_update_and_avatar():
    reset()
    token, _ = login("konglingjia")

    profile = client.get("/api/user/profile", headers=auth(token)).json()
    assert profile["code"] == 0
    assert profile["data"]["name"] == "晴天"
    assert profile["data"]["phone"] == "13800000001"

    updated = client.put(
        "/api/user/profile",
        headers=auth(token),
        json={
            "phone": "13900001111",
            "email": "new@example.com",
            "office_location": "上海分部",
        },
    ).json()
    assert updated["code"] == 0
    assert updated["data"]["phone"] == "13900001111"
    assert updated["data"]["email"] == "new@example.com"
    assert updated["data"]["office_location"] == "上海分部"

    invalid = client.put(
        "/api/user/profile",
        headers=auth(token),
        json={"phone": "13900001111", "email": "not-email", "office_location": "上海分部"},
    ).json()
    assert invalid["code"] == 2003

    avatar = client.post(
        "/api/user/avatar",
        headers=auth(token),
        json={"avatar_url": "https://example.com/avatar.png"},
    ).json()
    assert avatar["code"] == 0
    assert avatar["data"]["avatar_url"] == "https://example.com/avatar.png"

    invalid_avatar = client.post(
        "/api/user/avatar",
        headers=auth(token),
        json={"avatar_url": "ftp://example.com/avatar.txt"},
    ).json()
    assert invalid_avatar["code"] == 2001

    user_info = client.get("/api/auth/user-info", headers=auth(token)).json()["data"]
    assert user_info["avatar_url"] == "https://example.com/avatar.png"


def test_file_upload_avatar_and_bind_to_user_profile():
    reset()
    token, _ = login("konglingjia")

    uploaded = client.post(
        "/api/files/upload",
        headers=auth(token),
        data={"usage": "avatar"},
        files={"file": ("avatar.png", b"\x89PNG\r\n\x1a\nqingoa-avatar", "image/png")},
    ).json()
    assert uploaded["code"] == 0
    data = uploaded["data"]
    assert data["file_id"].startswith("file_")
    assert data["url"].startswith("/static/uploads/avatar/")
    assert data["filename"] == "avatar.png"
    assert data["mime_type"] == "image/png"
    assert data["usage"] == "avatar"

    asset = client.get(data["url"])
    assert asset.status_code == 200
    assert asset.content.startswith(b"\x89PNG")

    avatar = client.post(
        "/api/user/avatar",
        headers=auth(token),
        json={"file_id": data["file_id"]},
    ).json()
    assert avatar["code"] == 0
    assert avatar["data"]["avatar_url"] == data["url"]

    user_info = client.get("/api/auth/user-info", headers=auth(token)).json()["data"]
    assert user_info["avatar_url"] == data["url"]


def test_file_upload_avatar_rejects_non_image_and_preserves_avatar():
    reset()
    token, _ = login("konglingjia")
    client.post(
        "/api/user/avatar",
        headers=auth(token),
        json={"avatar_url": "https://example.com/avatar.png"},
    )

    rejected = client.post(
        "/api/files/upload",
        headers=auth(token),
        data={"usage": "avatar"},
        files={"file": ("avatar.txt", b"not-an-image", "text/plain")},
    ).json()
    assert rejected["code"] == 2011
    assert "头像文件必须" in rejected["msg"]

    profile = client.get("/api/user/profile", headers=auth(token)).json()["data"]
    assert profile["avatar_url"] == "https://example.com/avatar.png"


def test_static_avatar_asset_served():
    res = client.get("/static/avatars/qingoa_icon.png")
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("image/png")
    assert res.content.startswith(b"\x89PNG")


def test_notice_read_is_user_scoped():
    reset()
    token, _ = login("konglingjia")
    faraday_token, _ = login("faraday")

    unread = client.get("/api/home/unread-count", headers=auth(token)).json()
    assert unread["code"] == 0
    assert unread["data"]["notice_unread"] == 5

    marked = client.post("/api/notices/1/read", headers=auth(token)).json()
    assert marked["code"] == 0
    repeated = client.post("/api/notices/1/read", headers=auth(token)).json()
    assert repeated["code"] == 0

    notice = client.get("/api/notices/1", headers=auth(token)).json()["data"]
    assert notice["is_read"] is True
    list_body = client.get("/api/home/notices", headers=auth(token)).json()["data"]
    read_item = next(row for row in list_body["list"] if row["id"] == 1)
    assert read_item["is_read"] is True
    assert client.get("/api/home/unread-count", headers=auth(token)).json()["data"]["notice_unread"] == 4

    faraday_notice = client.get("/api/notices/1", headers=auth(faraday_token)).json()["data"]
    assert faraday_notice["is_read"] is False
    assert client.get("/api/home/unread-count", headers=auth(faraday_token)).json()["data"]["notice_unread"] == 5


def test_freeze_time_affects_clock_in_time():
    reset()
    client.post("/debug/freeze-time", json={"datetime": "2026-04-29 09:05:00"})
    token, _ = login("konglingjia")
    res = client.post(
        "/api/punch/clock",
        headers=auth(token),
        json={
            "lat": 39.811774,
            "lng": 116.295234,
            "device_id": "android_device_001",
            "punch_type": "clock_in",
        },
    )
    assert res.json()["data"]["punch_time"] == "2026-04-29 09:05:00"


def test_okr_list_detail_create_and_progress_update():
    reset()
    token, _ = login("konglingjia")

    initial = client.get("/api/okr/list", headers=auth(token)).json()
    assert initial["code"] == 0
    assert len(initial["data"]["list"]) >= 2
    first = initial["data"]["list"][0]
    assert first["progress"] >= 0
    assert first["kr_count"] >= 1

    detail = client.get(f"/api/okr/{first['id']}", headers=auth(token)).json()
    assert detail["code"] == 0
    assert detail["data"]["id"] == first["id"]
    assert detail["data"]["key_results"]

    created = client.post(
        "/api/okr/create",
        headers=auth(token),
        json={
            "title": "Q2 接口自动化",
            "description": "为透明 OA 补齐可追踪的接口用例",
            "period": "2026-Q2",
            "key_results": [
                {"title": "覆盖 OKR 核心接口", "target_value": 5, "unit": "个"},
                {"title": "完成 App 联调", "target_value": 100, "unit": "%"},
            ],
        },
    ).json()
    assert created["code"] == 0
    created_id = created["data"]["id"]

    created_detail = client.get(f"/api/okr/{created_id}", headers=auth(token)).json()["data"]
    assert created_detail["progress"] == 0
    kr_id = created_detail["key_results"][0]["id"]

    updated = client.put(
        f"/api/okr/{created_id}/key-results/{kr_id}",
        headers=auth(token),
        json={"current_value": 6},
    ).json()
    assert updated["code"] == 0
    assert updated["data"]["kr_progress"] == 100
    assert updated["data"]["okr_progress"] == 50


def test_okr_rejects_empty_key_results_and_cross_user_access():
    reset()
    token, _ = login("konglingjia")
    faraday_token, _ = login("faraday")

    invalid = client.post(
        "/api/okr/create",
        headers=auth(token),
        json={"title": "无 KR 目标", "period": "2026-Q2", "key_results": []},
    ).json()
    assert invalid["code"] == 1003

    faraday_list = client.get("/api/okr/list", headers=auth(faraday_token)).json()["data"]["list"]
    assert faraday_list
    blocked = client.get(f"/api/okr/{faraday_list[0]['id']}", headers=auth(token)).json()
    assert blocked["code"] == 1010


def test_okr_delete_soft_cancels_item():
    reset()
    token, _ = login("konglingjia")
    okr_id = client.get("/api/okr/list", headers=auth(token)).json()["data"]["list"][0]["id"]

    deleted = client.delete(f"/api/okr/{okr_id}", headers=auth(token)).json()
    assert deleted["code"] == 0

    detail = client.get(f"/api/okr/{okr_id}", headers=auth(token)).json()
    assert detail["code"] == 1010


def test_v16b_punch_status_appeal_two_level_approval_and_workflow():
    reset()
    client.post("/debug/freeze-time", json={"datetime": "2026-05-01 09:22:00"})
    token, data = login("konglingjia")
    manager_token, manager = login("manager")
    hr_token, hr = login("hr")

    late = client.post(
        "/api/punch/clock",
        headers=auth(token),
        json={
            "lat": 39.811774,
            "lng": 116.295234,
            "device_id": "android_device_001",
            "punch_type": "clock_in",
        },
    ).json()
    assert late["code"] == 0
    assert late["data"]["status"] == "late"

    appeal = client.post(
        "/api/punch/appeal",
        headers=auth(token),
        json={
            "punch_date": "2026-04-30",
            "punch_type": "clock_in",
            "reason": "车辆故障，申请补上班卡",
            "expect_time": "08:58:00",
        },
    ).json()
    assert appeal["code"] == 0
    appeal_id = appeal["data"]["appeal_id"]
    assert appeal["data"]["status"] == "submitted"

    duplicated = client.post(
        "/api/punch/appeal",
        headers=auth(token),
        json={
            "punch_date": "2026-04-30",
            "punch_type": "clock_in",
            "reason": "重复提交",
            "expect_time": "08:59:00",
        },
    ).json()
    assert duplicated["code"] == 1011

    pending_for_manager = client.get(
        "/api/punch/appeals/pending-review", headers=auth(manager_token)
    ).json()["data"]["list"]
    assert len(pending_for_manager) == 1
    assert pending_for_manager[0]["id"] == appeal_id
    assert pending_for_manager[0]["node_key"] == "manager_review"

    workflow_tasks = client.get("/api/workflow/tasks?bucket=todo", headers=auth(manager_token)).json()
    assert workflow_tasks["data"]["tasks"][0]["biz_type"] == "punch_appeal"

    manager_approved = client.post(
        f"/api/punch/appeals/{appeal_id}/review",
        headers=auth(manager_token),
        json={"action": "approve", "note": "已核实"},
    ).json()
    assert manager_approved["code"] == 0
    assert manager_approved["data"]["status"] == "manager_approved"
    assert client.get("/api/punch/records", headers=auth(token)).json()["data"]["total"] == 1

    state = client.get("/debug/state").json()["data"]
    instance = state["process_instances"][0]
    assert instance["status"] == "running"
    assert instance["current_node"] == "hr_review"
    assert any(task["assignee_id"] == hr["user_id"] and task["status"] == "todo" for task in state["process_tasks"])

    urged = client.post(
        f"/api/workflow/instances/{instance['id']}/urge",
        headers=auth(token),
    ).json()
    assert urged["code"] == 0
    assert urged["data"]["urged"] is True
    assert client.get("/api/workflow/tasks?bucket=urged", headers=auth(hr_token)).json()["data"]["tasks"]

    hr_approved = client.post(
        f"/api/punch/appeals/{appeal_id}/review",
        headers=auth(hr_token),
        json={"action": "approve", "note": "同意补卡"},
    ).json()
    assert hr_approved["code"] == 0
    assert hr_approved["data"]["status"] == "approved"

    records = client.get("/api/punch/records", headers=auth(token)).json()["data"]["list"]
    makeup = next(row for row in records if row["appeal_id"] == appeal_id)
    assert makeup["status"] == "makeup"
    assert makeup["source"] == "appeal"
    assert makeup["punch_time"] == "2026-04-30 08:58:00"

    state = client.get("/debug/state").json()["data"]
    assert state["process_instances"][0]["status"] == "completed"
    assert any(task["node_key"] == "hr_review" and task["status"] == "completed" for task in state["process_tasks"])

    summary = client.get("/api/punch/monthly-summary?month=2026-04", headers=auth(token)).json()
    assert summary["code"] == 0
    assert summary["data"]["month"] == "2026-04"

    recalculated = client.post(
        "/debug/attendance/recalculate",
        json={"username": "konglingjia", "month": "2026-04"},
    ).json()
    assert recalculated["code"] == 0
    assert recalculated["data"]["summary"]["month"] == "2026-04"


def test_v16b_manager_reject_ends_without_hr_task_or_makeup():
    reset()
    token, _ = login("konglingjia")
    manager_token, _ = login("manager")

    appeal = client.post(
        "/api/punch/appeal",
        headers=auth(token),
        json={
            "punch_date": "2026-05-02",
            "punch_type": "clock_out",
            "reason": "忘记打下班卡",
            "expect_time": "18:10:00",
        },
    ).json()
    appeal_id = appeal["data"]["appeal_id"]

    rejected = client.post(
        f"/api/punch/appeals/{appeal_id}/review",
        headers=auth(manager_token),
        json={"action": "reject", "note": "证明不足"},
    ).json()
    assert rejected["code"] == 0
    assert rejected["data"]["status"] == "rejected_by_manager"

    state = client.get("/debug/state").json()["data"]
    assert state["process_instances"][0]["status"] == "rejected"
    assert not any(task["node_key"] == "hr_review" for task in state["process_tasks"])
    assert client.get("/api/punch/records", headers=auth(token)).json()["data"]["total"] == 0

    again = client.post(
        f"/api/punch/appeals/{appeal_id}/review",
        headers=auth(manager_token),
        json={"action": "approve", "note": "再次审批"},
    ).json()
    assert again["code"] == 1014


def test_v16c_workflow_templates_task_actions_and_debug_state():
    reset()
    token, _ = login("konglingjia")
    manager_token, _ = login("manager")
    hr_token, _ = login("hr")

    templates = client.get("/api/workflow/templates", headers=auth(token)).json()
    assert templates["code"] == 0
    assert templates["data"]["templates"][0]["biz_type"] == "punch_appeal"
    assert templates["data"]["templates"][0]["nodes"][0]["key"] == "manager_review"
    debug_templates = client.get("/debug/workflow/templates").json()
    assert debug_templates["code"] == 0
    assert debug_templates["data"]["template_count"] >= 2
    assert debug_templates["data"]["templates"][1]["biz_type"] == "leave_request"

    appeal = client.post(
        "/api/punch/appeal",
        headers=auth(token),
        json={
            "punch_date": "2026-05-03",
            "punch_type": "clock_in",
            "reason": "地铁故障申请补卡",
            "expect_time": "09:02:00",
        },
    ).json()
    assert appeal["code"] == 0

    workflow_state = client.get("/debug/workflow/state?username=konglingjia").json()
    assert set(workflow_state["data"].keys()) == {
        "templates",
        "instances",
        "tasks",
        "instance_nodes",
        "punch_appeals",
        "leave_requests",
    }
    assert workflow_state["data"]["instances"][0]["status"] == "running"
    assert workflow_state["data"]["tasks"][0]["node_key"] == "manager_review"
    assert workflow_state["data"]["instance_nodes"][0]["node_title"] == "直属上级审批"

    manager_tasks = client.get("/api/workflow/tasks?bucket=todo", headers=auth(manager_token)).json()
    manager_task_id = manager_tasks["data"]["tasks"][0]["id"]
    manager_approved = client.post(
        f"/api/workflow/tasks/{manager_task_id}/approve",
        headers=auth(manager_token),
        json={"note": "上级通过"},
    ).json()
    assert manager_approved["code"] == 0
    assert manager_approved["data"]["status"] == "manager_approved"

    hr_tasks = client.get("/api/workflow/tasks?bucket=todo", headers=auth(hr_token)).json()
    hr_task_id = hr_tasks["data"]["tasks"][0]["id"]
    hr_rejected = client.post(
        f"/api/workflow/tasks/{hr_task_id}/reject",
        headers=auth(hr_token),
        json={"note": "HR 驳回"},
    ).json()
    assert hr_rejected["code"] == 0
    assert hr_rejected["data"]["status"] == "rejected_by_hr"

    completed = client.get("/api/workflow/instances?bucket=completed", headers=auth(token)).json()
    assert completed["data"]["instances"][0]["status"] == "rejected"


def test_v17_leave_two_days_manager_approve_and_debug_latest():
    reset()
    token, _ = login("konglingjia")
    manager_token, _ = login("manager")

    leave = client.post(
        "/api/leave/requests",
        headers=auth(token),
        json={
            "leave_type": "annual",
            "start_date": "2026-05-04",
            "end_date": "2026-05-05",
            "reason": "家中有事，申请年假",
        },
    ).json()
    assert leave["code"] == 0
    assert leave["data"]["days"] == 2.0
    assert leave["data"]["status"] == "submitted"
    instance_id = leave["data"]["process_instance_id"]

    detail = client.get(f"/api/workflow/instances/{instance_id}", headers=auth(token)).json()
    assert detail["code"] == 0
    assert detail["data"]["business"]["leave_type_label"] == "年假"
    assert any(action["action"] == "cancel" for action in detail["data"]["available_actions"])

    task_id = client.get("/api/workflow/tasks?bucket=todo", headers=auth(manager_token)).json()["data"]["tasks"][0]["id"]
    manager_detail = client.get(f"/api/workflow/instances/{instance_id}", headers=auth(manager_token)).json()
    assert {action["action"] for action in manager_detail["data"]["available_actions"]} == {
        "approve",
        "reject",
        "return",
    }

    approved = client.post(
        f"/api/workflow/tasks/{task_id}/approve",
        headers=auth(manager_token),
        json={"note": "同意"},
    ).json()
    assert approved["code"] == 0
    assert approved["data"]["status"] == "approved"

    state = client.get("/debug/workflow/state?username=konglingjia").json()["data"]
    assert state["instances"][0]["status"] == "completed"
    assert state["leave_requests"][0]["status"] == "approved"
    assert not client.get("/api/workflow/tasks?bucket=todo", headers=auth(login("hr")[0])).json()["data"]["tasks"]

    latest = client.get("/debug/leave/latest?username=konglingjia").json()
    assert latest["code"] == 0
    assert latest["data"]["leave"]["process_instance_id"] == instance_id
    assert latest["data"]["leave"]["status"] == "approved"


def test_v171_leave_attachment_submit_and_manager_can_see():
    reset()
    token, _ = login("konglingjia")
    manager_token, _ = login("manager")

    uploaded = client.post(
        "/api/files/upload",
        headers=auth(token),
        data={"usage": "leave_attachment"},
        files={"file": ("sick-note.txt", b"medical note for leave", "text/plain")},
    ).json()
    assert uploaded["code"] == 0
    file_id = uploaded["data"]["file_id"]

    leave = client.post(
        "/api/leave/requests",
        headers=auth(token),
        json={
            "leave_type": "sick",
            "start_date": "2026-05-04",
            "end_date": "2026-05-05",
            "reason": "病假两天，附诊断说明",
            "attachment_file_ids": [file_id],
        },
    ).json()
    assert leave["code"] == 0
    assert leave["data"]["attachments"][0]["file_id"] == file_id
    assert leave["data"]["attachments"][0]["filename"] == "sick-note.txt"
    instance_id = leave["data"]["process_instance_id"]

    applicant_detail = client.get(f"/api/workflow/instances/{instance_id}", headers=auth(token)).json()
    assert applicant_detail["data"]["business"]["attachments"][0]["file_id"] == file_id

    manager_detail = client.get(f"/api/workflow/instances/{instance_id}", headers=auth(manager_token)).json()
    assert manager_detail["data"]["business"]["attachments"][0]["url"].startswith("/static/uploads/leave_attachment/")

    task_id = client.get("/api/workflow/tasks?bucket=todo", headers=auth(manager_token)).json()["data"]["tasks"][0]["id"]
    approved = client.post(
        f"/api/workflow/tasks/{task_id}/approve",
        headers=auth(manager_token),
        json={"note": "附件齐全，同意"},
    ).json()
    assert approved["code"] == 0
    assert approved["data"]["status"] == "approved"
    assert approved["data"]["attachments"][0]["file_id"] == file_id

    latest = client.get("/debug/leave/latest?username=konglingjia").json()
    assert latest["data"]["leave"]["attachments"][0]["filename"] == "sick-note.txt"


def test_v171_leave_attachment_rejects_wrong_usage_and_keeps_workflow_empty():
    reset()
    token, _ = login("konglingjia")

    uploaded = client.post(
        "/api/files/upload",
        headers=auth(token),
        data={"usage": "avatar"},
        files={"file": ("avatar.png", b"\x89PNG\r\n\x1a\navatar", "image/png")},
    ).json()
    assert uploaded["code"] == 0

    leave = client.post(
        "/api/leave/requests",
        headers=auth(token),
        json={
            "leave_type": "annual",
            "start_date": "2026-05-04",
            "end_date": "2026-05-05",
            "reason": "使用错误用途文件，应失败",
            "attachment_file_ids": [uploaded["data"]["file_id"]],
        },
    ).json()
    assert leave["code"] == 2011
    assert "用途不匹配" in leave["msg"]

    state = client.get("/debug/workflow/state?username=konglingjia").json()["data"]
    assert state["instances"] == []
    assert state["leave_requests"] == []


def test_v18_im_search_add_friend_and_single_conversation_dedup():
    reset()
    token, _ = login("konglingjia")
    manager_token, _ = login("manager")

    search = client.get("/api/im/users/search?q=manager", headers=auth(token)).json()
    assert search["code"] == 0
    assert search["data"]["list"][0]["username"] == "manager"
    assert search["data"]["list"][0]["is_friend"] is False

    add = client.post("/api/im/friends", headers=auth(token), json={"friend_user_id": 5}).json()
    assert add["code"] == 0
    assert add["data"]["username"] == "manager"
    assert add["data"]["is_friend"] is True

    duplicate_add = client.post("/api/im/friends", headers=auth(token), json={"friend_user_id": 5}).json()
    assert duplicate_add["code"] == 0

    state = client.get("/debug/im/state?username=konglingjia").json()["data"]
    assert [row["friend_user_id"] for row in state["friends"]] == [5]

    first = client.post("/api/im/conversations/single", headers=auth(token), json={"peer_user_id": 5}).json()
    assert first["code"] == 0
    conversation_id = first["data"]["id"]

    second = client.post("/api/im/conversations/single", headers=auth(manager_token), json={"peer_user_id": 1}).json()
    assert second["code"] == 0
    assert second["data"]["id"] == conversation_id

    manager_state = client.get("/debug/im/state?username=manager").json()["data"]
    assert [row["friend_user_id"] for row in manager_state["friends"]] == [1]
    assert manager_state["conversations"][0]["id"] == conversation_id


def test_v18_im_single_conversation_auto_adds_friend_for_non_friend_pair():
    reset()
    token, _ = login("konglingjia")

    conversation = client.post("/api/im/conversations/single", headers=auth(token), json={"peer_user_id": 6}).json()
    assert conversation["code"] == 0
    assert conversation["data"]["peer"]["username"] == "hr"

    state = client.get("/debug/im/state?username=konglingjia").json()["data"]
    assert [row["friend_user_id"] for row in state["friends"]] == [6]
    hr_state = client.get("/debug/im/state?username=hr").json()["data"]
    assert [row["friend_user_id"] for row in hr_state["friends"]] == [1]


def test_v18_im_text_message_unread_and_mark_read():
    reset()
    token, _ = login("konglingjia")
    manager_token, _ = login("manager")
    conversation = client.post("/api/im/conversations/single", headers=auth(token), json={"peer_user_id": 5}).json()["data"]
    conversation_id = conversation["id"]

    sent = client.post(
        f"/api/im/conversations/{conversation_id}/messages",
        headers=auth(token),
        json={"message_type": "text", "content": "今天下午开会吗"},
    ).json()
    assert sent["code"] == 0
    assert sent["data"]["message_type"] == "text"
    assert sent["data"]["content"] == "今天下午开会吗"
    assert sent["data"]["file_id"] is None

    sender_conversations = client.get("/api/im/conversations", headers=auth(token)).json()["data"]["list"]
    assert sender_conversations[0]["unread_count"] == 0
    assert sender_conversations[0]["last_message"]["summary"] == "今天下午开会吗"

    receiver_conversations = client.get("/api/im/conversations", headers=auth(manager_token)).json()["data"]["list"]
    assert receiver_conversations[0]["unread_count"] == 1
    assert receiver_conversations[0]["last_message"]["summary"] == "今天下午开会吗"

    messages = client.get(f"/api/im/conversations/{conversation_id}/messages", headers=auth(manager_token)).json()
    assert messages["code"] == 0
    assert messages["data"]["list"][0]["sender_id"] == 1

    read = client.post(f"/api/im/conversations/{conversation_id}/read", headers=auth(manager_token), json={}).json()
    assert read["code"] == 0
    assert read["data"]["last_read_message_id"] == sent["data"]["id"]

    read_back = client.post(
        f"/api/im/conversations/{conversation_id}/read",
        headers=auth(manager_token),
        json={"last_read_message_id": 0},
    ).json()
    assert read_back["code"] == 0
    assert read_back["data"]["last_read_message_id"] == sent["data"]["id"]

    receiver_conversations = client.get("/api/im/conversations", headers=auth(manager_token)).json()["data"]["list"]
    assert receiver_conversations[0]["unread_count"] == 0


def test_badges_im_unread():
    reset()
    token, _ = login("konglingjia")
    manager_token, _ = login("manager")
    conversation_id = client.post(
        "/api/im/conversations/single",
        headers=auth(token),
        json={"peer_user_id": 5},
    ).json()["data"]["id"]

    client.post(
        f"/api/im/conversations/{conversation_id}/messages",
        headers=auth(token),
        json={"message_type": "text", "content": "请看一下 1.8 红点"},
    )

    badges = client.get("/api/badges/summary", headers=auth(manager_token)).json()
    assert badges["code"] == 0
    assert badges["data"]["im"]["unread_total"] == 1


def test_badges_im_after_read():
    reset()
    token, _ = login("konglingjia")
    manager_token, _ = login("manager")
    conversation_id = client.post(
        "/api/im/conversations/single",
        headers=auth(token),
        json={"peer_user_id": 5},
    ).json()["data"]["id"]

    client.post(
        f"/api/im/conversations/{conversation_id}/messages",
        headers=auth(token),
        json={"message_type": "text", "content": "读完要清红点"},
    )
    before = client.get("/api/badges/summary", headers=auth(manager_token)).json()["data"]
    assert before["im"]["unread_total"] == 1

    read = client.post(f"/api/im/conversations/{conversation_id}/read", headers=auth(manager_token), json={}).json()
    assert read["code"] == 0
    after = client.get("/api/badges/summary", headers=auth(manager_token)).json()["data"]
    assert after["im"]["unread_total"] == 0


def test_badges_workflow_counts():
    reset()
    token, _ = login("konglingjia")
    manager_token, _ = login("manager")
    leave = client.post(
        "/api/leave/requests",
        headers=auth(token),
        json={
            "leave_type": "annual",
            "start_date": "2026-05-11",
            "end_date": "2026-05-12",
            "reason": "验证流程红点数字",
        },
    ).json()["data"]

    applicant_badges = client.get("/api/badges/summary", headers=auth(token)).json()["data"]
    assert applicant_badges["workflow"]["processing"] == 1
    assert applicant_badges["workflow"]["returned"] == 0
    assert applicant_badges["workflow"]["actionable_total"] == 0

    manager_badges = client.get("/api/badges/summary", headers=auth(manager_token)).json()["data"]
    assert manager_badges["workflow"]["todo"] == 1
    assert manager_badges["workflow"]["actionable_total"] == 1

    task_id = client.get("/api/workflow/tasks?bucket=todo", headers=auth(manager_token)).json()["data"]["tasks"][0]["id"]
    returned = client.post(
        f"/api/workflow/tasks/{task_id}/return",
        headers=auth(manager_token),
        json={"note": "补充说明"},
    ).json()
    assert returned["code"] == 0
    assert returned["data"]["process_instance_id"] == leave["process_instance_id"]

    applicant_badges = client.get("/api/badges/summary", headers=auth(token)).json()["data"]
    assert applicant_badges["workflow"]["processing"] == 0
    assert applicant_badges["workflow"]["returned"] == 1
    assert applicant_badges["workflow"]["actionable_total"] == 1


def test_badges_urged_not_double_counted():
    reset()
    token, _ = login("konglingjia")
    manager_token, _ = login("manager")
    leave = client.post(
        "/api/leave/requests",
        headers=auth(token),
        json={
            "leave_type": "annual",
            "start_date": "2026-05-13",
            "end_date": "2026-05-13",
            "reason": "验证催办不重复计数",
        },
    ).json()["data"]
    urged = client.post(
        f"/api/workflow/instances/{leave['process_instance_id']}/urge",
        headers=auth(token),
    ).json()
    assert urged["code"] == 0

    badges = client.get("/api/badges/summary", headers=auth(manager_token)).json()["data"]["workflow"]
    assert badges["todo"] == 1
    assert badges["urged"] == 1
    assert badges["returned"] == 0
    assert badges["actionable_total"] == 1


def test_badges_mine_punch_appeal():
    reset()
    token, _ = login("konglingjia")
    manager_token, _ = login("manager")
    appeal = client.post(
        "/api/punch/appeal",
        headers=auth(token),
        json={
            "punch_date": "2026-05-14",
            "punch_type": "clock_in",
            "reason": "忘记上班打卡，申请补卡",
            "expect_time": "08:58:00",
        },
    ).json()
    assert appeal["code"] == 0

    manager_badges = client.get("/api/badges/summary", headers=auth(manager_token)).json()["data"]
    assert manager_badges["mine"]["punch_appeal_review"] == 1
    assert manager_badges["workflow"]["todo"] == 1


def test_v18_im_image_message_uses_uploaded_file_and_empty_content():
    reset()
    token, _ = login("konglingjia")
    conversation = client.post("/api/im/conversations/single", headers=auth(token), json={"peer_user_id": 5}).json()["data"]

    rejected_upload = client.post(
        "/api/files/upload",
        headers=auth(token),
        data={"usage": "im_image"},
        files={"file": ("note.txt", b"not an image", "text/plain")},
    ).json()
    assert rejected_upload["code"] == 2011
    assert "IM 图片必须" in rejected_upload["msg"]

    uploaded = client.post(
        "/api/files/upload",
        headers=auth(token),
        data={"usage": "im_image"},
        files={"file": ("chat.png", b"\x89PNG\r\n\x1a\nqingoa-im", "image/png")},
    ).json()
    assert uploaded["code"] == 0
    file_id = uploaded["data"]["file_id"]
    assert uploaded["data"]["usage"] == "im_image"
    assert uploaded["data"]["url"].startswith("/static/uploads/im_image/")

    sent = client.post(
        f"/api/im/conversations/{conversation['id']}/messages",
        headers=auth(token),
        json={"message_type": "image", "file_id": file_id, "content": "should be ignored"},
    ).json()
    assert sent["code"] == 0
    assert sent["data"]["message_type"] == "image"
    assert sent["data"]["content"] == ""
    assert sent["data"]["file_id"] == file_id
    assert sent["data"]["file"]["url"] == uploaded["data"]["url"]

    conversations = client.get("/api/im/conversations", headers=auth(token)).json()["data"]["list"]
    assert conversations[0]["last_message"]["summary"] == "[图片]"


def test_v18_im_permission_boundaries_and_invalid_self_operations():
    reset()
    token, _ = login("konglingjia")
    thanos_token, _ = login("thanos")
    conversation = client.post("/api/im/conversations/single", headers=auth(token), json={"peer_user_id": 5}).json()["data"]

    self_friend = client.post("/api/im/friends", headers=auth(token), json={"friend_user_id": 1}).json()
    assert self_friend["code"] == 1003

    self_conversation = client.post("/api/im/conversations/single", headers=auth(token), json={"peer_user_id": 1}).json()
    assert self_conversation["code"] == 1003

    outsider_messages = client.get(
        f"/api/im/conversations/{conversation['id']}/messages",
        headers=auth(thanos_token),
    ).json()
    assert outsider_messages["code"] == 1010

    outsider_send = client.post(
        f"/api/im/conversations/{conversation['id']}/messages",
        headers=auth(thanos_token),
        json={"message_type": "text", "content": "我不在这个会话"},
    ).json()
    assert outsider_send["code"] == 1010


def test_v18_im_debug_reset_state_and_preserves_non_im_uploads():
    reset()
    token, _ = login("konglingjia")
    client.post("/api/im/conversations/single", headers=auth(token), json={"peer_user_id": 5})
    avatar = client.post(
        "/api/files/upload",
        headers=auth(token),
        data={"usage": "avatar"},
        files={"file": ("avatar.png", b"\x89PNG\r\n\x1a\navatar", "image/png")},
    ).json()["data"]
    im_image = client.post(
        "/api/files/upload",
        headers=auth(token),
        data={"usage": "im_image"},
        files={"file": ("chat.png", b"\x89PNG\r\n\x1a\nchat", "image/png")},
    ).json()["data"]
    conversation_id = client.get("/api/im/conversations", headers=auth(token)).json()["data"]["list"][0]["id"]
    client.post(
        f"/api/im/conversations/{conversation_id}/messages",
        headers=auth(token),
        json={"message_type": "image", "file_id": im_image["file_id"]},
    )

    state = client.get("/debug/im/state?username=konglingjia").json()["data"]
    assert state["friends"]
    assert state["conversations"]
    assert state["messages"]

    reset_im = client.post("/debug/im/reset", json={"usernames": ["konglingjia"]}).json()
    assert reset_im["code"] == 0
    assert reset_im["data"]["deleted_count"] > 0

    state = client.get("/debug/im/state?username=konglingjia").json()["data"]
    assert state["friends"] == []
    assert state["conversations"] == []
    assert state["messages"] == []

    avatar_bind = client.post("/api/user/avatar", headers=auth(token), json={"file_id": avatar["file_id"]}).json()
    assert avatar_bind["code"] == 0
    assert avatar_bind["data"]["avatar_url"] == avatar["url"]


def test_v17_leave_four_days_requires_hr_review():
    reset()
    token, _ = login("konglingjia")
    manager_token, _ = login("manager")
    hr_token, _ = login("hr")

    leave = client.post(
        "/api/leave/requests",
        headers=auth(token),
        json={
            "leave_type": "sick",
            "start_date": "2026-05-04",
            "end_date": "2026-05-07",
            "reason": "病假需要休养四天",
        },
    ).json()["data"]
    assert leave["days"] == 4.0

    task_id = client.get("/api/workflow/tasks?bucket=todo", headers=auth(manager_token)).json()["data"]["tasks"][0]["id"]
    manager_approved = client.post(
        f"/api/workflow/tasks/{task_id}/approve",
        headers=auth(manager_token),
        json={"note": "直属上级同意"},
    ).json()
    assert manager_approved["code"] == 0
    assert manager_approved["data"]["status"] == "manager_approved"

    hr_tasks = client.get("/api/workflow/tasks?bucket=todo", headers=auth(hr_token)).json()["data"]["tasks"]
    assert len(hr_tasks) == 1
    assert hr_tasks[0]["node_key"] == "hr_review"

    hr_approved = client.post(
        f"/api/workflow/tasks/{hr_tasks[0]['id']}/approve",
        headers=auth(hr_token),
        json={"note": "HR 同意"},
    ).json()
    assert hr_approved["code"] == 0
    assert hr_approved["data"]["status"] == "approved"


def test_v17_leave_return_resubmit_recalculates_hr_route_and_cancel():
    reset()
    token, _ = login("konglingjia")
    manager_token, _ = login("manager")
    hr_token, _ = login("hr")

    leave = client.post(
        "/api/leave/requests",
        headers=auth(token),
        json={
            "leave_type": "personal",
            "start_date": "2026-05-04",
            "end_date": "2026-05-07",
            "reason": "事假四天，先提交审批",
        },
    ).json()["data"]
    instance_id = leave["process_instance_id"]

    task_id = client.get("/api/workflow/tasks?bucket=todo", headers=auth(manager_token)).json()["data"]["tasks"][0]["id"]
    returned = client.post(
        f"/api/workflow/tasks/{task_id}/return",
        headers=auth(manager_token),
        json={"note": "请缩短请假区间"},
    ).json()
    assert returned["code"] == 0
    assert returned["data"]["status"] == "returned"

    returned_instances = client.get("/api/workflow/instances?bucket=returned", headers=auth(token)).json()
    assert returned_instances["data"]["instances"][0]["id"] == instance_id
    detail = client.get(f"/api/workflow/instances/{instance_id}", headers=auth(token)).json()
    assert {action["action"] for action in detail["data"]["available_actions"]} == {"resubmit", "cancel"}

    resubmitted = client.post(
        f"/api/workflow/instances/{instance_id}/resubmit",
        headers=auth(token),
        json={
            "leave_type": "personal",
            "start_date": "2026-05-04",
            "end_date": "2026-05-05",
            "reason": "改为两天事假",
        },
    ).json()
    assert resubmitted["code"] == 0
    assert resubmitted["data"]["days"] == 2.0
    assert resubmitted["data"]["status"] == "submitted"

    new_task_id = client.get("/api/workflow/tasks?bucket=todo", headers=auth(manager_token)).json()["data"]["tasks"][0]["id"]
    approved = client.post(
        f"/api/workflow/tasks/{new_task_id}/approve",
        headers=auth(manager_token),
        json={"note": "修改后同意"},
    ).json()
    assert approved["code"] == 0
    assert approved["data"]["status"] == "approved"
    assert client.get("/api/workflow/tasks?bucket=todo", headers=auth(hr_token)).json()["data"]["tasks"] == []

    cancelled = client.post(
        "/api/leave/requests",
        headers=auth(token),
        json={
            "leave_type": "annual",
            "start_date": "2026-05-08",
            "end_date": "2026-05-08",
            "reason": "创建后取消",
        },
    ).json()["data"]
    cancel = client.post(
        f"/api/leave/requests/{cancelled['id']}/cancel",
        headers=auth(token),
    ).json()
    assert cancel["code"] == 0
    assert cancel["data"]["status"] == "cancelled"


def test_v17_leave_validation_and_debug_workflow_reset():
    reset()
    token, _ = login("konglingjia")

    invalid_type = client.post(
        "/api/leave/requests",
        headers=auth(token),
        json={
            "leave_type": "travel",
            "start_date": "2026-05-04",
            "end_date": "2026-05-04",
            "reason": "非法类型",
        },
    ).json()
    assert invalid_type["code"] == 1025

    invalid_date = client.post(
        "/api/leave/requests",
        headers=auth(token),
        json={
            "leave_type": "annual",
            "start_date": "2026-05-06",
            "end_date": "2026-05-04",
            "reason": "日期倒置",
        },
    ).json()
    assert invalid_date["code"] == 1021

    created = client.post(
        "/api/leave/requests",
        headers=auth(token),
        json={
            "leave_type": "annual",
            "start_date": "2026-05-04",
            "end_date": "2026-05-04",
            "reason": "用于重置验证",
        },
    ).json()
    assert created["code"] == 0

    reset_workflow = client.post("/debug/workflow/reset?username=konglingjia").json()
    assert reset_workflow["code"] == 0
    state = client.get("/debug/workflow/state?username=konglingjia").json()["data"]
    assert state["instances"] == []
    assert state["tasks"] == []
    assert state["leave_requests"] == []
