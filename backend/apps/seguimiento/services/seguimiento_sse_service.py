"""Pub/sub in-process para SSE mapa operador (RF-SEG-007)."""

from __future__ import annotations

import json
import queue
import threading
from collections.abc import Iterator
from typing import Any

_lock = threading.Lock()
_subscribers: list[queue.Queue[str]] = []


class SeguimientoSseService:
    def publish(self, event_type: str, data: dict[str, Any]) -> None:
        message = f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
        with _lock:
            dead: list[queue.Queue[str]] = []
            for sub in _subscribers:
                try:
                    sub.put_nowait(message)
                except queue.Full:
                    dead.append(sub)
            for sub in dead:
                _subscribers.remove(sub)

    def stream_events(self) -> Iterator[str]:
        sub: queue.Queue[str] = queue.Queue(maxsize=64)
        with _lock:
            _subscribers.append(sub)
        try:
            yield ": connected\n\n"
            while True:
                try:
                    yield sub.get(timeout=25)
                except queue.Empty:
                    yield ": heartbeat\n\n"
        finally:
            with _lock:
                if sub in _subscribers:
                    _subscribers.remove(sub)
