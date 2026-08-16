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

    def query(
        self,
        sql: str,
        params: dict[str, Any] | None = None,
        settings: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Ejecuta un SELECT de solo lectura y devuelve filas como lista de dicts.

        `params` son los **parámetros con tipo de ClickHouse**: la consulta
        escribe `{desde:Date}` y aquí viaja como `param_desde`. El servidor los
        liga; no se concatenan al SQL. Es la diferencia entre un valor y un
        fragmento de consulta — con interpolación, un valor que contenga SQL
        **es** SQL.

        `settings` son ajustes de servidor para esta consulta (`readonly`,
        `max_execution_time`).
        """
        stripped = sql.strip().rstrip(";")
        argumentos: dict[str, Any] = {"database": self.database}
        argumentos.update(settings or {})
        for nombre, valor in (params or {}).items():
            argumentos[f"param_{nombre}"] = valor
        response = requests.post(
            self.url,
            params=argumentos,
            data=f"{stripped} FORMAT JSONEachRow".encode("utf-8"),
            auth=self.auth,
            timeout=10,
        )
        response.raise_for_status()
        text = response.text.strip()
        if not text:
            return []
        return [json.loads(line) for line in text.splitlines()]
