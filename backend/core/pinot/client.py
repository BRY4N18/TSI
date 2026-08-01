"""Apache Pinot read-only client."""

from __future__ import annotations

import re
from typing import Any

import requests


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


_NON_FINITE_TOKENS = {"Infinity", "-Infinity", "NaN"}

# Pinot aplica un `LIMIT 10` implícito a toda consulta que no declare uno, y lo
# hace en silencio: la respuesta no distingue "hay 10 filas" de "hay 10 de 500".
# Un repositorio que filtra o pagina en Python sobre ese resultado trabaja sobre
# un recorte arbitrario (sin ORDER BY el subconjunto ni siquiera es estable), así
# que devuelve datos incompletos sin error visible. Se fuerza un tope explícito
# alto para que el recorte lo decida el repositorio, no el broker.
DEFAULT_QUERY_LIMIT = 10_000
_LIMIT_RE = re.compile(r"\blimit\b\s+\d+\s*$", re.IGNORECASE)
# Pinot's default "no value" sentinels when column-based null handling is
# disabled (enableColumnBasedNullHandling: false, the default in our schemas).
_INT_NULL_SENTINEL = -2147483648
_LONG_NULL_SENTINEL = -9223372036854775808


def _coerce_value(value: Any, data_type: str) -> Any:
    """Coerce a raw Pinot broker value to a native Python type.

    The broker's JSON response encodes every cell as whatever JSON allows,
    which means INT/LONG/DOUBLE/BOOLEAN columns often arrive as strings
    (and non-finite aggregates like MAX() over zero rows arrive as the
    literal string "-Infinity"). Unset STRING columns come back as the
    literal text "null" (not JSON null), and unset INT/LONG columns come
    back as Pinot's sentinel min-value. Repositories are written assuming
    native Python types (int, float, bool, None), matching what the
    mock_pinot fixture already produces in tests.
    """
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


class PinotClient:
    """Read-only Pinot SQL client. Writes are forbidden at this layer."""

    def __init__(self, broker_url: str | None = None):
        from django.conf import settings

        self.broker_url = broker_url or settings.PINOT_BROKER_URL

    @staticmethod
    def _with_explicit_limit(sql: str) -> str:
        """Añade `LIMIT DEFAULT_QUERY_LIMIT` si la consulta no declara uno.

        Sin esto Pinot recorta a 10 filas en silencio (ver DEFAULT_QUERY_LIMIT).
        Las consultas que ya traen su propio LIMIT se respetan tal cual.
        """
        stripped = sql.strip().rstrip(";").rstrip()
        if _LIMIT_RE.search(stripped):
            return stripped
        return f"{stripped} LIMIT {DEFAULT_QUERY_LIMIT}"

    def query(self, sql: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """
        Execute a read-only SQL query against Pinot.

        The Pinot broker's /query/sql endpoint has no native bind-parameter
        support, so %(name)s placeholders are interpolated client-side into
        safely-quoted SQL literals before sending the request.
        Tests patch this method via the mock_pinot fixture.
        """
        rendered_sql = sql % {k: _quote_literal(v) for k, v in (params or {}).items()}
        rendered_sql = self._with_explicit_limit(rendered_sql)

        response = requests.post(
            f"{self.broker_url}/query/sql",
            json={"sql": rendered_sql},
            timeout=10,
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
