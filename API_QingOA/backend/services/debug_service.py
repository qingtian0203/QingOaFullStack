from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from backend.core import time_provider


@dataclass
class Scenario:
    id: str
    method: str
    path: str
    response: dict[str, Any]
    times: int = 1
    user_id: int | None = None
    delay_ms: int = 0
    http_status: int = 200

    @property
    def times_remaining(self) -> int:
        return self.times

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "method": self.method,
            "path": self.path,
            "times_remaining": self.times_remaining,
            "user_id": self.user_id,
            "delay_ms": self.delay_ms,
            "http_status": self.http_status,
            "response": self.response,
        }


@dataclass
class DebugState:
    scenarios: dict[str, Scenario] = field(default_factory=dict)
    requests: deque = field(default_factory=lambda: deque(maxlen=50))
    next_request_id: int = 1


state = DebugState()


def reset_runtime_state() -> None:
    state.scenarios.clear()
    state.requests.clear()
    state.next_request_id = 1
    time_provider.unfreeze()


def add_scenario(
    *,
    method: str,
    path: str,
    response: dict[str, Any],
    times: int = 1,
    user_id: int | None = None,
    delay_ms: int = 0,
    http_status: int = 200,
) -> Scenario:
    scenario = Scenario(
        id=str(uuid4()),
        method=method.upper(),
        path=path,
        response=response,
        times=times,
        user_id=user_id,
        delay_ms=delay_ms,
        http_status=http_status,
    )
    state.scenarios[scenario.id] = scenario
    return scenario


def list_scenarios() -> list[dict[str, Any]]:
    return [scenario.to_dict() for scenario in state.scenarios.values()]


def clear_scenarios() -> None:
    state.scenarios.clear()


def delete_scenario(scenario_id: str) -> bool:
    return state.scenarios.pop(scenario_id, None) is not None


def match_scenario(method: str, path: str, user_id: int | None) -> Scenario | None:
    method = method.upper()
    for scenario in list(state.scenarios.values()):
        if scenario.method != method:
            continue
        if scenario.path != path:
            continue
        if scenario.user_id is not None and scenario.user_id != user_id:
            continue
        if scenario.times == 0:
            state.scenarios.pop(scenario.id, None)
            continue
        if scenario.times > 0:
            scenario.times -= 1
            if scenario.times == 0:
                state.scenarios.pop(scenario.id, None)
        return scenario
    return None


def add_request_log(
    *,
    method: str,
    path: str,
    user_id: int | None,
    auth_present: bool,
    request_body: Any,
    response_code: int | None,
    response_body: Any,
    duration_ms: int,
    scenario_injected: bool,
) -> None:
    entry = {
        "id": state.next_request_id,
        "time": time_provider.fmt(time_provider.now()),
        "method": method.upper(),
        "path": path,
        "user_id": user_id,
        "auth_present": auth_present,
        "request_body": _mask_sensitive(request_body),
        "response_code": response_code,
        "response_body": response_body,
        "duration_ms": duration_ms,
        "scenario_injected": scenario_injected,
    }
    state.next_request_id += 1
    state.requests.appendleft(entry)


def list_request_logs() -> list[dict[str, Any]]:
    return list(state.requests)


def _mask_sensitive(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: "***" if key.lower() in {"password"} else _mask_sensitive(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_mask_sensitive(item) for item in value]
    return value
