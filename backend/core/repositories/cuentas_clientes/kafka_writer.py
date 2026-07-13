"""Kafka write adapter — sole write channel for domain entities."""

from __future__ import annotations

import json
import threading
from typing import Any

from kafka import KafkaProducer

_producer: KafkaProducer | None = None
_producer_lock = threading.Lock()


def _get_producer(bootstrap_servers: str) -> KafkaProducer:
    """Lazily create a single shared KafkaProducer for the process."""
    global _producer
    if _producer is None:
        with _producer_lock:
            if _producer is None:
                _producer = KafkaProducer(
                    bootstrap_servers=bootstrap_servers,
                    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                    linger_ms=10,
                )
    return _producer


class KafkaWriter:
    """Publishes domain events to Kafka topics."""

    def __init__(self, bootstrap_servers: str | None = None):
        from django.conf import settings

        self.bootstrap_servers = bootstrap_servers or settings.KAFKA_BOOTSTRAP_SERVERS
        self._published: list[dict[str, Any]] = []

    def publish(self, topic: str, payload: dict[str, Any]) -> None:
        """
        Publish a domain event to the given Kafka topic.

        Tests patch this method (or use the mock_kafka fixture) and never
        reach the real producer below.
        """
        producer = _get_producer(self.bootstrap_servers)
        future = producer.send(topic, value=payload)
        future.get(timeout=10)
        self._published.append({"topic": topic, "payload": payload})

    @property
    def published_messages(self) -> list[dict[str, Any]]:
        """Return messages published during this instance lifetime (useful in tests)."""
        return list(self._published)
