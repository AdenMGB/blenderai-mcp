"""TCP JSON client for the Blender addon bridge."""

from __future__ import annotations

import json
import os
import socket
import uuid
from typing import Any


class BlenderBridgeError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")


class BlenderBridgeClient:
    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        auth_token: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.host = host or os.environ.get("BLENDERAI_HOST", "127.0.0.1")
        self.port = int(port or os.environ.get("BLENDERAI_PORT", "9876"))
        self.auth_token = auth_token or os.environ.get("BLENDERAI_AUTH_TOKEN", "")
        self.timeout = timeout
        self._sock: socket.socket | None = None

    def connect(self) -> None:
        if self._sock:
            return
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)
        try:
            sock.connect((self.host, self.port))
        except (OSError, socket.timeout) as exc:
            raise BlenderBridgeError(
                "TIMEOUT",
                f"Cannot connect to Blender addon at {self.host}:{self.port}: {exc}",
            ) from exc
        self._sock = sock

    def close(self) -> None:
        if self._sock:
            try:
                self._sock.close()
            except OSError:
                pass
            self._sock = None

    def call(self, method: str, params: dict[str, Any] | None = None) -> Any:
        self.connect()
        assert self._sock is not None

        request_id = str(uuid.uuid4())
        payload = {
            "id": request_id,
            "method": method,
            "params": {**(params or {}), "auth_token": self.auth_token},
        }

        line = json.dumps(payload) + "\n"
        try:
            self._sock.sendall(line.encode("utf-8"))
            response = self._read_line()
        except socket.timeout as exc:
            raise BlenderBridgeError("TIMEOUT", f"Request timed out: {method}") from exc
        except OSError as exc:
            self.close()
            raise BlenderBridgeError("TIMEOUT", f"Connection error: {exc}") from exc

        try:
            data = json.loads(response)
        except json.JSONDecodeError as exc:
            raise BlenderBridgeError("EXECUTION_ERROR", f"Invalid JSON response: {exc}") from exc

        if not data.get("ok"):
            err = data.get("error") or {}
            raise BlenderBridgeError(
                err.get("code", "EXECUTION_ERROR"),
                err.get("message", "Unknown error"),
            )

        return data.get("data")

    def _read_line(self) -> str:
        assert self._sock is not None
        buffer = ""
        while "\n" not in buffer:
            chunk = self._sock.recv(65536)
            if not chunk:
                raise BlenderBridgeError("TIMEOUT", "Connection closed by Blender addon")
            buffer += chunk.decode("utf-8")
        line, _ = buffer.split("\n", 1)
        return line.strip()


_default_client: BlenderBridgeClient | None = None


def get_client() -> BlenderBridgeClient:
    global _default_client
    if _default_client is None:
        _default_client = BlenderBridgeClient()
    return _default_client
