"""Cliente HTTP mínimo a Pinot para los DAGs de informes tácticos compuestos.

Autocontenido a propósito (ver plan.md, Structure Decision / research.md §2):
el contenedor `tactico-airflow-scheduler` no tiene montado `backend/`, así que
no se puede reutilizar `core.pinot.client.PinotClient` (depende de Django).
Mismo comportamiento de fondo: LIMIT explícito por defecto, solo lectura.
"""

from __future__ import annotations

import os
import re
from typing import Any

import requests

PINOT_BROKER_URL = os.environ.get("PINOT_BROKER_URL", "http://pinot-broker:8099")
DEFAULT_QUERY_LIMIT = 10_000
_LIMIT_RE = re.compile(r"\blimit\b\s+\d+\s*$", re.IGNORECASE)
_NON_FINITE_TOKENS = {"Infinity", "-Infinity", "NaN"}
_INT_NULL_SENTINEL = -2147483648
_LONG_NULL_SENTINEL = -9223372036854775808


def _quote_literal(value: Any) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, (list, tuple, set)):
        return "(" + ", ".join(_quote_literal(v) for v in value) + ")"
    escaped = str(value).replace("'", "''")
    return f"'{escaped}'"


def _coerce_value(value: Any, data_type: str) -> Any:
    if value is None:
        return None
    if isinstance(value, str) and value in _NON_FINITE_TOKENS:
        return None
    if data_type == "STRING":
        return None if value == "null" else value
    if data_type in ("INT", "LONG"):
        ivalue = int(value)
        if ivalue in (_INT_NULL_SENTINEL, _LONG_NULL_SENTINEL):
            return None
        return ivalue
    if data_type in ("FLOAT", "DOUBLE"):
        return float(value)
    if data_type == "BOOLEAN":
        return value if isinstance(value, bool) else str(value).lower() == "true"
    return value


def _with_explicit_limit(sql: str) -> str:
    stripped = sql.strip().rstrip(";").rstrip()
    if _LIMIT_RE.search(stripped):
        return stripped
    return f"{stripped} LIMIT {DEFAULT_QUERY_LIMIT}"


def query_pinot(sql: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Ejecuta una consulta SQL de solo lectura contra el broker de Pinot."""
    rendered_sql = sql % {k: _quote_literal(v) for k, v in (params or {}).items()}
    rendered_sql = _with_explicit_limit(rendered_sql)

    response = requests.post(
        f"{PINOT_BROKER_URL}/query/sql",
        json={"sql": rendered_sql},
        timeout=30,
    )
    response.raise_for_status()
    body = response.json()

    exceptions = body.get("exceptions")
    if exceptions:
        raise RuntimeError(f"Pinot query failed: {exceptions}")

    result_table = body.get("resultTable")
    if not result_table:
        return []

    columns = result_table["dataSchema"]["columnNames"]
    types = result_table["dataSchema"]["columnDataTypes"]
    rows = result_table["rows"]
    return [
        {col: _coerce_value(val, typ) for col, val, typ in zip(columns, row, types)}
        for row in rows
    ]
