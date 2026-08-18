"""Roles y asignación por usuario: claves y nombres de rol, **sin identidad**."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Iterable, Mapping

from lib.pinot_http_client import query_pinot

LIMITE = 50_000

CONSULTA_ROLES = f"""
    SELECT idrol, rol, descripcion, activo
    FROM Dim_Rol
    LIMIT {LIMITE}
"""

CONSULTA_ASIGNACIONES = f"""
    SELECT idusuario, idrol
    FROM Dim_Usuario_Rol
    LIMIT {LIMITE}
"""


def extraer(consultar: Callable[[str], list[dict]] = query_pinot) -> dict[str, list[dict]]:
    return {
        "roles": consultar(CONSULTA_ROLES),
        "asignaciones": consultar(CONSULTA_ASIGNACIONES),
    }


def _activo(valor: Any) -> int:
    return 1 if valor in (True, 1, "true", "1", "True") else 0


def construir_roles(
    filas: Iterable[Mapping[str, Any]], ahora: datetime
) -> list[dict]:
    version = ahora.strftime("%Y-%m-%d %H:%M:%S")
    return [
        {
            "idrol": int(r["idrol"]),
            "rol": r.get("rol") or "",
            "descripcion": r.get("descripcion") or None,
            "es_activo": _activo(r.get("activo", True)),
            "version": version,
        }
        for r in filas
    ]


def construir_asignaciones(
    asignaciones: Iterable[Mapping[str, Any]],
    roles: Iterable[Mapping[str, Any]],
    ahora: datetime,
) -> list[dict]:
    version = ahora.strftime("%Y-%m-%d %H:%M:%S")
    nombre = {int(r["idrol"]): r.get("rol") or "" for r in roles}
    filas = []
    for a in asignaciones:
        uid = a.get("idusuario")
        rid = a.get("idrol")
        if uid is None or rid is None:
            continue
        rid = int(rid)
        filas.append({
            "idusuario": int(uid),
            "idrol": rid,
            "rol": nombre.get(rid, ""),
            "es_activo": 1,
            "version": version,
        })
    return filas
