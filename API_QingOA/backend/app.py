from __future__ import annotations

import asyncio
import json
import time
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from sqlalchemy.orm import Session

from backend.core.config import APP_NAME
from backend.core.errors import ApiError, BAD_REQUEST, INTERNAL_ERROR
from backend.core.response import fail, json_response, ok
from backend.db.database import SessionLocal, create_tables
from backend.db.seed import seed_if_empty
from backend.routers import auth, debug, home, mine, notices, okr, punch, user
from backend.services import auth_service, debug_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    with SessionLocal() as db:
        seed_if_empty(db)
    yield


app = FastAPI(title=APP_NAME, version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def debug_observability_middleware(request: Request, call_next):
    start = time.perf_counter()
    body_bytes = await request.body()
    request_body = _decode_json(body_bytes)
    user_id = _user_id_from_request(request)
    auth_present = _authorization_present(request)
    scenario_injected = False

    async def receive():
        return {"type": "http.request", "body": body_bytes, "more_body": False}

    request._receive = receive

    is_debug_path = request.url.path.startswith("/debug")
    scenario = None if is_debug_path else debug_service.match_scenario(request.method, request.url.path, user_id)
    if scenario is not None:
        scenario_injected = True
        if scenario.delay_ms:
            await asyncio.sleep(scenario.delay_ms / 1000)
        response_body = scenario.response
        duration_ms = int((time.perf_counter() - start) * 1000)
        if not is_debug_path:
            debug_service.add_request_log(
                method=request.method,
                path=request.url.path,
                user_id=user_id,
                auth_present=auth_present,
                request_body=request_body,
                response_code=_api_code(response_body),
                response_body=response_body,
                duration_ms=duration_ms,
                scenario_injected=True,
            )
        return json_response(response_body, status_code=scenario.http_status)

    response = await call_next(request)
    response_body_bytes = b""
    async for chunk in response.body_iterator:
        response_body_bytes += chunk
    response_body = _decode_json(response_body_bytes)
    duration_ms = int((time.perf_counter() - start) * 1000)
    if not is_debug_path:
        debug_service.add_request_log(
            method=request.method,
            path=request.url.path,
            user_id=user_id,
            auth_present=auth_present,
            request_body=request_body,
            response_code=_api_code(response_body),
            response_body=response_body,
            duration_ms=duration_ms,
            scenario_injected=scenario_injected,
        )

    headers = dict(response.headers)
    headers.pop("content-length", None)
    return Response(
        content=response_body_bytes,
        status_code=response.status_code,
        headers=headers,
        media_type=response.media_type,
        background=response.background,
    )


@app.exception_handler(ApiError)
async def api_error_handler(request: Request, exc: ApiError):
    return json_response(fail(exc.code, exc.msg, exc.data), status_code=exc.http_status)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    return json_response(fail(BAD_REQUEST, _validation_error_message(exc.errors())))


@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception):
    return json_response(fail(INTERNAL_ERROR, f"服务器内部错误：{exc}"))


@app.get("/")
def root():
    return ok({"name": APP_NAME, "docs": "/docs"})


app.include_router(auth.router)
app.include_router(home.router)
app.include_router(mine.router)
app.include_router(notices.router)
app.include_router(okr.router)
app.include_router(user.router)
app.include_router(punch.router)
app.include_router(debug.router)


def _decode_json(body: bytes) -> Any:
    if not body:
        return None
    try:
        return json.loads(body.decode("utf-8"))
    except Exception:
        return body.decode("utf-8", errors="ignore")


def _api_code(body: Any) -> int | None:
    if isinstance(body, dict) and isinstance(body.get("code"), int):
        return body["code"]
    return None


def _authorization_present(request: Request) -> bool:
    authorization = request.headers.get("authorization")
    return bool(authorization and authorization.lower().startswith("bearer ") and authorization[7:].strip())


def _validation_error_message(errors: list[dict[str, Any]]) -> str:
    field_names = {
        "lat": "纬度",
        "lng": "经度",
        "device_id": "设备 ID",
        "punch_type": "打卡类型",
    }
    messages: list[str] = []
    for error in errors:
        loc = error.get("loc") or []
        field = str(loc[-1]) if loc else "参数"
        label = field_names.get(field, field)
        error_type = error.get("type")
        ctx = error.get("ctx") or {}
        if error_type == "less_than_equal" and "le" in ctx:
            messages.append(f"{label}不能大于 {ctx['le']}")
        elif error_type == "greater_than_equal" and "ge" in ctx:
            messages.append(f"{label}不能小于 {ctx['ge']}")
        else:
            messages.append(f"{label}格式错误")
    return "参数错误：" + "；".join(messages) if messages else "参数缺失或格式错误"


def _user_id_from_request(request: Request) -> int | None:
    authorization = request.headers.get("authorization")
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    token = authorization[7:].strip()
    if not token:
        return None
    db: Session = SessionLocal()
    try:
        user = auth_service.get_user_by_token(db, token)
        return user.id if user else None
    finally:
        db.close()
