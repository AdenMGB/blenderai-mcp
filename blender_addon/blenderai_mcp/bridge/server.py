"""TCP JSON bridge server and main-thread dispatcher."""

from __future__ import annotations

import json
import socket
import threading
import traceback
from typing import Any

import bpy

from .protocol import Request, error_response, success_response
from .queue import PendingCommand, command_queue
from ..handlers import dispatch_safe

_server_thread: threading.Thread | None = None
_server_socket: socket.socket | None = None
_timer_registered = False
_running = False
_status_message = "Stopped"
_connection_counter = 0
_connection_lock = threading.Lock()


def is_running() -> bool:
    return _running


def get_status() -> str:
    return _status_message


def _next_connection_id() -> int:
    global _connection_counter
    with _connection_lock:
        _connection_counter += 1
        return _connection_counter


def _set_status(msg: str) -> None:
    global _status_message
    _status_message = msg


def _send_json(conn: socket.socket, payload: dict[str, Any]) -> None:
    data = (json.dumps(payload) + "\n").encode("utf-8")
    conn.sendall(data)


def _handle_client(conn: socket.socket, addr: tuple) -> None:
    conn_id = _next_connection_id()
    buffer = ""

    def reply_callback(response: dict[str, Any]) -> None:
        try:
            _send_json(conn, response)
        except OSError:
            pass

    command_queue.register_connection(conn_id, reply_callback)

    try:
        while _running:
            try:
                chunk = conn.recv(65536)
                if not chunk:
                    break
                buffer += chunk.decode("utf-8")
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if not line:
                        continue
                    _enqueue_line(line, conn_id, reply_callback)
            except socket.timeout:
                continue
            except OSError:
                break
    finally:
        command_queue.unregister_connection(conn_id)
        try:
            conn.close()
        except OSError:
            pass


def _enqueue_line(
    line: str,
    conn_id: int,
    reply_callback,
) -> None:
    try:
        raw = json.loads(line)
        request = Request.from_dict(raw)
    except json.JSONDecodeError as exc:
        reply_callback(error_response("", ErrorCode.INVALID_PARAMS, f"Invalid JSON: {exc}"))
        return

    if not request.id or not request.method:
        reply_callback(
            error_response(
                request.id,
                ErrorCode.INVALID_PARAMS,
                "Request must include id and method",
            )
        )
        return

    cmd = PendingCommand(
        request_id=request.id,
        method=request.method,
        params=request.params,
        connection_id=conn_id,
        reply_callback=reply_callback,
    )
    command_queue.enqueue(cmd)


def _dispatcher_timer() -> float | None:
    """Called on Blender main thread every ~5ms."""
    if not _running:
        return None

    prefs = bpy.context.preferences.addons["blenderai_mcp"].preferences
    auth_token = prefs.auth_token  # type: ignore[attr-defined]

    for cmd in command_queue.dequeue_all():
        ok, data, err_code, err_msg = dispatch_safe(
            cmd.method, cmd.params, auth_token
        )
        if ok:
            response = success_response(cmd.request_id, data)
        else:
            response = error_response(cmd.request_id, err_code or "EXECUTION_ERROR", err_msg or "")
        cmd.reply_callback(response)

    return 0.005


def _accept_loop(host: str, port: int) -> None:
    global _server_socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((host, port))
        sock.listen(8)
        sock.settimeout(1.0)
        _server_socket = sock
        _set_status(f"Listening on {host}:{port}")

        while _running:
            try:
                conn, addr = sock.accept()
                conn.settimeout(1.0)
                client_thread = threading.Thread(
                    target=_handle_client,
                    args=(conn, addr),
                    daemon=True,
                    name=f"BlenderAI-Client-{addr}",
                )
                client_thread.start()
            except socket.timeout:
                continue
            except OSError:
                if _running:
                    traceback.print_exc()
                break
    except OSError as exc:
        _set_status(f"Error: {exc}")
    finally:
        if _server_socket:
            try:
                _server_socket.close()
            except OSError:
                pass
            _server_socket = None


def start_server(host: str = "127.0.0.1", port: int = 9876) -> bool:
    global _server_thread, _timer_registered, _running

    if _running:
        return True

    _running = True
    _set_status("Starting...")

    _server_thread = threading.Thread(
        target=_accept_loop,
        args=(host, port),
        daemon=True,
        name="BlenderAI-Server",
    )
    _server_thread.start()

    if not _timer_registered:
        bpy.app.timers.register(_dispatcher_timer, first_interval=0.005, persistent=True)
        _timer_registered = True

    return True


def stop_server() -> None:
    global _running, _server_thread, _timer_registered

    _running = False
    _set_status("Stopped")

    if _server_socket:
        try:
            _server_socket.close()
        except OSError:
            pass

    if _server_thread and _server_thread.is_alive():
        _server_thread.join(timeout=2.0)
    _server_thread = None

    if _timer_registered:
        try:
            bpy.app.timers.unregister(_dispatcher_timer)
        except Exception:
            pass
        _timer_registered = False


# Import ErrorCode for JSON errors in socket thread
from .protocol import ErrorCode  # noqa: E402
