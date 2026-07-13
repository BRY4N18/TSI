"""Kafka consumer handler registry for despacho domain."""

from __future__ import annotations

from typing import Any, Callable

_HANDLERS: dict[str, Callable[[dict[str, Any]], Any]] = {}


def register_consumer(topic: str, handler: Callable[[dict[str, Any]], Any]) -> None:
    _HANDLERS[topic] = handler


def get_consumer_handlers() -> dict[str, Callable[[dict[str, Any]], Any]]:
    return dict(_HANDLERS)
