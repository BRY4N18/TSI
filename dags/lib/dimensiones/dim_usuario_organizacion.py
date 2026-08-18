"""Pertenencia usuario↔organización **sin identidad**.

Carga **todos** los usuarios, no solo los que tienen fila en
`Dim_Usuario_Cliente`. Sin los demás es imposible calcular la cobertura
(hoy el 9,5 %). La pertenencia sale **solo** de esa relación explícita,
nunca de `Dim_Cliente.admin_local_id`.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Iterable, Mapping

from lib.pinot_http_client import query_pinot

LIMITE = 50_000

CONSULTA_USUARIOS = f"""
    SELECT idusuario, activo
    FROM Dim_Usuarios
    LIMIT {LIMITE}
"""

#: Solo la relación explícita. `admin_local_id` **no se pide**.
CONSULTA_PERTENENCIA = f"""
    SELECT idusuario, idcliente, activo
    FROM Dim_Usuario_Cliente
    LIMIT {LIMITE}
"""


def extraer(consultar: Callable[[str], list[dict]] = query_pinot) -> dict[str, list[dict]]:
    return {
        "usuarios": consultar(CONSULTA_USUARIOS),
        "pertenencia": consultar(CONSULTA_PERTENENCIA),
    }


def _activo(valor: Any) -> int:
    return 1 if valor in (True, 1, "true", "1", "True") else 0


def construir(
    datos: Mapping[str, Iterable[Mapping[str, Any]]], ahora: datetime
) -> list[dict]:
    version = ahora.strftime("%Y-%m-%d %H:%M:%S")
    por_usuario: dict[int, dict] = {}
    for p in datos.get("pertenencia", []):
        uid = p.get("idusuario")
        cid = p.get("idcliente")
        if uid is None or cid is None:
            continue
        if not _activo(p.get("activo", True)):
            continue
        por_usuario[int(uid)] = {
            "idusuario": int(uid),
            "idcliente": int(cid),
            "tiene_pertenencia": 1,
        }

    filas = []
    for u in datos.get("usuarios", []):
        uid = int(u["idusuario"])
        base = por_usuario.get(uid, {
            "idusuario": uid,
            "idcliente": None,
            "tiene_pertenencia": 0,
        })
        filas.append({
            **base,
            "es_activo": _activo(u.get("activo", True)),
            "version": version,
        })
    return filas
