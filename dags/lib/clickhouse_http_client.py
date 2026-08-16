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


def query_clickhouse(sql: str, params: dict | None = None) -> list[dict]:
    """Ejecuta un SELECT y devuelve filas como lista de dicts (FORMAT JSONEachRow).

    `params` son los **parámetros con tipo de ClickHouse**: la consulta escribe
    `{desde:Date}` y aquí viaja como `param_desde`, ligado por el servidor. Es lo
    que permite ejecutar las consultas del catálogo tal como están escritas, sin
    reconstruirlas — si hubiera que interpolarlas para correrlas, la prueba
    estaría comprobando una consulta distinta de la que se publica.
    """
    stripped = sql.strip().rstrip(";")
    argumentos = {
        "database": CLICKHOUSE_DB,
        # Sin esto, ClickHouse devuelve los enteros de 64 bits **entrecomillados**
        # y `count()` es `UInt64`: un conteo de 2 llega como la cadena `"2"`.
        # Entrecomilla por defecto para no perder precisión por encima de 2^53
        # —real para identificadores, irrelevante para conteos—.
        #
        # El backend fija el mismo ajuste al leer el catálogo. Que los dos
        # coincidan no es cosmético: la prueba de contraste compara la cifra del
        # endpoint con la de la consulta, y `"2" != 2` la haría fallar por una
        # diferencia de serialización en vez de por una de cálculo — que es
        # justo la clase de ruido que hace desconfiar de la prueba y no del dato.
        "output_format_json_quote_64bit_integers": "0",
    }
    for nombre, valor in (params or {}).items():
        argumentos[f"param_{nombre}"] = valor
    response = requests.post(
        CLICKHOUSE_URL,
        params=argumentos,
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
