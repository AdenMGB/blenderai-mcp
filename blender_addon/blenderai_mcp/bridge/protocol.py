"""JSON request/response protocol for the TCP bridge."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


class ErrorCode:
    AUTH_FAILED = "AUTH_FAILED"
    INVALID_PARAMS = "INVALID_PARAMS"
    OBJECT_NOT_FOUND = "OBJECT_NOT_FOUND"
    TIMEOUT = "TIMEOUT"
    METHOD_NOT_FOUND = "METHOD_NOT_FOUND"
    EXECUTION_ERROR = "EXECUTION_ERROR"
    DESTRUCTIVE_NOT_CONFIRMED = "DESTRUCTIVE_NOT_CONFIRMED"


ERROR_CODES = frozenset(
    {
        ErrorCode.AUTH_FAILED,
        ErrorCode.INVALID_PARAMS,
        ErrorCode.OBJECT_NOT_FOUND,
        ErrorCode.TIMEOUT,
        ErrorCode.METHOD_NOT_FOUND,
        ErrorCode.EXECUTION_ERROR,
        ErrorCode.DESTRUCTIVE_NOT_CONFIRMED,
    }
)


@dataclass
class Request:
    id: str
    method: str
    params: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> Request:
        return cls(
            id=str(raw.get("id", "")),
            method=str(raw.get("method", "")),
            params=raw.get("params") if isinstance(raw.get("params"), dict) else {},
        )


def encode_message(payload: dict[str, Any]) -> bytes:
    return (json.dumps(payload, separators=(",", ":")) + "\n").encode("utf-8")


def decode_message(line: bytes) -> dict[str, Any]:
    return json.loads(line.decode("utf-8"))


def success_response(request_id: str, data: Any) -> dict[str, Any]:
    return {"id": request_id, "ok": True, "data": data}


def error_response(request_id: str, code: str, message: str) -> dict[str, Any]:
    return {"id": request_id, "ok": False, "error": {"code": code, "message": message}}


def make_success(request_id: str, data: Any) -> dict[str, Any]:
    return success_response(request_id, data)


def make_error(
    request_id: str,
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    error: dict[str, Any] = {"code": code, "message": message}
    if details:
        error["details"] = details
    return {"id": request_id, "ok": False, "error": error}


def validate_request(payload: dict[str, Any]) -> str | None:
    if not isinstance(payload, dict):
        return "Request must be a JSON object"
    if "id" not in payload:
        return "Missing required field: id"
    if "method" not in payload:
        return "Missing required field: method"
    if not isinstance(payload.get("method"), str):
        return "Field 'method' must be a string"
    params = payload.get("params")
    if params is not None and not isinstance(params, dict):
        return "Field 'params' must be an object"
    return None
