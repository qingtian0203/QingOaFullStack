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
    assert menus[1]["enabled"] is False
    assert menus[1]["disabled_reason"] == "功能开发中"
    assert all(menu.get("target") != "PunchRecordListActivity" for menu in menus)

    res = client.get("/api/mine/menu", headers=auth(token))
    body = res.json()
    assert body["code"] == 0
    mine_menus = body["data"]["menus"]
    assert len(mine_menus) == 1
    assert mine_menus[0]["target"] == "PunchRecordListActivity"
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
