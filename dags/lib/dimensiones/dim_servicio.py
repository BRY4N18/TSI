"""`dim_servicio`: catálogo de servicios/APIs afectados por un ticket."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Iterable, Mapping

from lib.hechos.comun import FORMATO
from lib.pinot_http_client import query_pinot

LIMITE = 10_000

CONSULTA = f"""
    SELECT id_servicio, nombre, tipo, activo
    FROM Dim_Servicio
    LIMIT {LIMITE}
"""


def extraer(consultar: Callable[[str], list[dict]] = query_pinot) -> list[dict]:
    return consultar(CONSULTA)


def construir(filas_origen: Iterable[Mapping[str, Any]], ahora: datetime) -> list[dict]:
    version = ahora.strftime(FORMATO)
    filas = []
    for f in filas_origen:
        filas.append({
            "id_servicio": int(f["id_servicio"]),
            "nombre": (f.get("nombre") or "").strip() or "",
            "tipo": (f.get("tipo") or None) or None,
            "es_activo": 1 if f.get("activo") in (True, 1, "true", "1") else 0,
            "version": version,
        })
    return filas
