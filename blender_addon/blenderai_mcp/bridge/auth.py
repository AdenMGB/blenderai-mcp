"""Bearer token authentication for bridge requests."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .protocol import ErrorCode


@dataclass(frozen=True)
class AuthError:
    code: str
    message: str


def extract_token(params: dict[str, Any] | None) -> str | None:
    if not params:
        return None
    token = params.get("auth_token")
    if isinstance(token, str) and token:
        return token
    return None


def validate_token(params: dict[str, Any] | None, expected_token: str) -> AuthError | None:
    if not expected_token:
        return AuthError(ErrorCode.AUTH_FAILED, "Addon auth token is not configured")
    provided = extract_token(params)
    if not provided:
        return AuthError(ErrorCode.AUTH_FAILED, "Missing auth_token in params")
    if provided != expected_token:
        return AuthError(ErrorCode.AUTH_FAILED, "Invalid auth token")
    return None


def verify_token(params: dict[str, Any] | None) -> tuple[bool, str | None]:
    from .. import preferences

    expected = preferences.get_preferences().auth_token
    error = validate_token(params, expected)
    if error:
        return False, error.message
    return True, None
