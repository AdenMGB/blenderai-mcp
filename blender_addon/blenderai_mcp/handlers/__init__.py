"""Handler registry and dispatch."""

from __future__ import annotations

from typing import Any

from ..bridge.auth import validate_token
from ..bridge.protocol import ErrorCode
from .registry import get_handler, register_all_handlers, unregister_all_handlers

__all__ = [
    "dispatch",
    "dispatch_safe",
    "register_handlers",
    "unregister_handlers",
]


def register_handlers() -> None:
    register_all_handlers()


def unregister_handlers() -> None:
    unregister_all_handlers()


def dispatch(method: str, params: dict, auth_token: str) -> Any:
    auth_error = validate_token(params, auth_token)
    if auth_error:
        raise PermissionError(auth_error.code, auth_error.message)

    handler = get_handler(method)
    if handler is None:
        raise LookupError(f"Unknown method: {method}")

    return handler.fn(params)


def dispatch_safe(
    method: str, params: dict, auth_token: str
) -> tuple[bool, Any, str | None, str | None]:
    """Returns (ok, data, error_code, error_message)."""
    try:
        data = dispatch(method, params, auth_token)
        return True, data, None, None
    except PermissionError as exc:
        code = exc.args[0] if exc.args else ErrorCode.AUTH_FAILED
        msg = exc.args[1] if len(exc.args) > 1 else str(exc)
        return False, None, str(code), msg
    except LookupError as exc:
        msg = str(exc)
        if msg.startswith("Unknown method:"):
            return False, None, ErrorCode.METHOD_NOT_FOUND, msg
        return False, None, ErrorCode.OBJECT_NOT_FOUND, msg
    except (ValueError, TypeError) as exc:
        return False, None, ErrorCode.INVALID_PARAMS, str(exc)
    except Exception as exc:
        return False, None, ErrorCode.EXECUTION_ERROR, str(exc)
