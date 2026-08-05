"""ClickHouse read-only HTTP client — mismo patrón que core.pinot.client.PinotClient."""

from __future__ import annotations

import json
from typing import Any

import requests


class ClickHouseClient:
    """Solo lectura desde Django: los DAGs de Airflow son el único escritor."""

    def __init__(self, url: str | None = None):
        from django.conf import settings

        self.url = url or settings.CLICKHOUSE_URL
        self.database = settings.CLICKHOUSE_DB
        self.auth = (settings.CLICKHOUSE_USER, settings.CLICKHOUSE_PASSWORD)

    def query(self, sql: str) -> list[dict[str, Any]]:
        """Ejecuta un SELECT de solo lectura y devuelve filas como lista de dicts."""
        stripped = sql.strip().rstrip(";")
        response = requests.post(
            self.url,
            params={"database": self.database},
            data=f"{stripped} FORMAT JSONEachRow".encode("utf-8"),
            auth=self.auth,
            timeout=10,
        )
        response.raise_for_status()
        text = response.text.strip()
        if not text:
            return []
        return [json.loads(line) for line in text.splitlines()]
