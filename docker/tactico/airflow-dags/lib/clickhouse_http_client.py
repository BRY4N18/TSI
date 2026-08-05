"""Cliente HTTP mínimo a ClickHouse para los DAGs de informes tácticos compuestos.

Autocontenido (research.md §1-2): usa la interfaz HTTP nativa de ClickHouse en
vez de un driver de terceros, para no añadir dependencias a la imagen de
Airflow. A diferencia de `pinot_http_client`, este SÍ escribe (INSERT/DDL) —
es el único punto de escritura del stack `tactico` hacia ClickHouse.
"""

from __future__ import annotations

import json
import os

import requests

CLICKHOUSE_URL = os.environ.get("CLICKHOUSE_URL", "http://tactico-clickhouse:8123")
CLICKHOUSE_USER = os.environ.get("CLICKHOUSE_USER", "tactico")
CLICKHOUSE_PASSWORD = os.environ.get("CLICKHOUSE_PASSWORD", "tactico")
CLICKHOUSE_DB = os.environ.get("CLICKHOUSE_DB", "tsi_tactico")

_AUTH = (CLICKHOUSE_USER, CLICKHOUSE_PASSWORD)


def execute_clickhouse(sql: str) -> None:
    """Ejecuta DDL o INSERT (sin resultado esperado)."""
    response = requests.post(
        CLICKHOUSE_URL,
        params={"database": CLICKHOUSE_DB},
        data=sql.encode("utf-8"),
        auth=_AUTH,
        timeout=30,
    )
    if response.status_code != 200:
        raise RuntimeError(f"ClickHouse execute failed ({response.status_code}): {response.text}")


def query_clickhouse(sql: str) -> list[dict]:
    """Ejecuta un SELECT y devuelve filas como lista de dicts (FORMAT JSONEachRow)."""
    stripped = sql.strip().rstrip(";")
    response = requests.post(
        CLICKHOUSE_URL,
        params={"database": CLICKHOUSE_DB},
        data=f"{stripped} FORMAT JSONEachRow".encode("utf-8"),
        auth=_AUTH,
        timeout=30,
    )
    if response.status_code != 200:
        raise RuntimeError(f"ClickHouse query failed ({response.status_code}): {response.text}")
    text = response.text.strip()
    if not text:
        return []
    return [json.loads(line) for line in text.splitlines()]


def insert_rows(table: str, rows: list[dict]) -> None:
    """INSERT batch de filas (lista de dicts) en `table`, vía FORMAT JSONEachRow."""
    if not rows:
        return
    payload = "\n".join(json.dumps(row) for row in rows)
    sql = f"INSERT INTO {table} FORMAT JSONEachRow\n{payload}"
    execute_clickhouse(sql)
