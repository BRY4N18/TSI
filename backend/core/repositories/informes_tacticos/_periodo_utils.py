"""Conversión de `periodo` (resultado de DATETRUNC en Pinot) a string de fecha.

Pinot devuelve DATETRUNC(...) como epoch milliseconds (LONG), no como string
de fecha — encontrado en producción real durante la revisión final (los tests
con `mock_pinot` no lo detectaron porque el mock simulaba el resultado como
string directamente). Compartido por `registro_repository.py` y
`seguimiento_repository.py`, que agrupan por período con DATETRUNC.
"""

from __future__ import annotations

from datetime import datetime, timezone


def periodo_str(epoch_ms: int) -> str:
    return datetime.fromtimestamp(epoch_ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
