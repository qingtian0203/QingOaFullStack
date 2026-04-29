from __future__ import annotations

from typing import Any

from fastapi.responses import JSONResponse


def payload(code: int = 0, msg: str = "success", data: Any = None) -> dict[str, Any]:
    return {"code": code, "msg": msg, "data": data}


def ok(data: Any = None, msg: str = "success") -> dict[str, Any]:
    return payload(0, msg, data)


def fail(code: int, msg: str, data: Any = None) -> dict[str, Any]:
    return payload(code, msg, data)


def json_response(body: dict[str, Any], status_code: int = 200) -> JSONResponse:
    return JSONResponse(content=body, status_code=status_code)

