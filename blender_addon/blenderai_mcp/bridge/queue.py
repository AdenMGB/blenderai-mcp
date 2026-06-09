"""Thread-safe command queue for main-thread dispatch."""

from __future__ import annotations

import queue
import threading
from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class PendingCommand:
    request_id: str
    method: str
    params: dict[str, Any]
    connection_id: int
    reply_callback: Callable[[dict[str, Any]], None]


class CommandQueue:
    def __init__(self) -> None:
        self._queue: queue.Queue[PendingCommand] = queue.Queue()
        self._connections: dict[int, Callable[[dict[str, Any]], None]] = {}
        self._lock = threading.Lock()

    def register_connection(
        self,
        connection_id: int,
        reply_callback: Callable[[dict[str, Any]], None],
    ) -> None:
        with self._lock:
            self._connections[connection_id] = reply_callback

    def unregister_connection(self, connection_id: int) -> None:
        with self._lock:
            self._connections.pop(connection_id, None)

    def enqueue(self, command: PendingCommand) -> None:
        self._queue.put(command)

    def dequeue_all(self, max_items: int = 32) -> list[PendingCommand]:
        items: list[PendingCommand] = []
        while len(items) < max_items:
            try:
                items.append(self._queue.get_nowait())
            except queue.Empty:
                break
        return items


command_queue = CommandQueue()
