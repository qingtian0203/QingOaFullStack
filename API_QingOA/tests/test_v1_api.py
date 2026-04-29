from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app import app


client = TestClient(app)


def reset():
    res = client.post("/debug/reset-data")
    assert res.status_code == 200
    assert res.json()["code"] == 0


def login(username="admin", password="123456"):
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
    assert data["username"] == "admin"

    res = client.get("/api/auth/user-info", headers=auth(token))
    assert res.json()["data"]["name"] == "张三"

    res = client.get("/api/home/menu", headers=auth(token))
    body = res.json()
    assert body["code"] == 0
    menus = body["data"]["menus"]
    assert menus[0]["enabled"] is True
    assert menus[1]["enabled"] is False
    assert menus[1]["disabled_reason"] == "功能开发中"


def test_success_clock_in_and_debug_state():
    reset()
    token, data = login("admin")

    res = client.post(
        "/api/punch/clock-in",
        headers=auth(token),
        json={"lat": 39.9042, "lng": 116.4074, "device_id": "android_device_001"},
    )
    body = res.json()
    assert body["code"] == 0
    assert body["msg"] == "打卡成功"
    assert body["data"]["point_name"] == "总部大楼"

    state = client.get("/debug/state").json()["data"]
    assert any(row["user_id"] == data["user_id"] for row in state["today_punch_records"])

    logs = client.get("/debug/requests").json()["data"]["requests"]
    assert logs[0]["path"] == "/api/punch/clock-in"
    assert logs[0]["response_code"] == 0


def test_faraday_out_of_range_no_record():
    reset()
    token, data = login("faraday")
    res = client.post(
        "/api/punch/clock-in",
        headers=auth(token),
        json={"lat": 39.8000, "lng": 116.2000, "device_id": "android_device_001"},
    )
    body = res.json()
    assert body["code"] == 1004
    assert "不在打卡范围内" in body["msg"]

    state = client.get("/debug/state").json()["data"]
    assert not any(row["user_id"] == data["user_id"] for row in state["today_punch_records"])


def test_injected_token_expired_for_user_info():
    reset()
    token, data = login("admin")
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


def test_freeze_time_affects_clock_in_time():
    reset()
    client.post("/debug/freeze-time", json={"datetime": "2026-04-29 09:05:00"})
    token, _ = login("admin")
    res = client.post(
        "/api/punch/clock-in",
        headers=auth(token),
        json={"lat": 39.9042, "lng": 116.4074, "device_id": "android_device_001"},
    )
    assert res.json()["data"]["punch_time"] == "2026-04-29 09:05:00"

