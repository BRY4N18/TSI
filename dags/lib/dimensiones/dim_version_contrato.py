"""`dim_version_contrato`: clave (servicio, versión). Época cero → retiro ausente."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Iterable, Mapping

from lib.hechos.comun import FORMATO, a_datetime, texto_fecha
from lib.pinot_http_client import query_pinot

LIMITE = 10_000

CONSULTA_VERSIONES = f"""
    SELECT idversion, id_servicio, version, estado,
           fecha_publicacion, fecha_retiro
    FROM Dim_VersionContratoAPI
    LIMIT {LIMITE}
"""

CONSULTA_SERVICIOS = f"""
    SELECT id_servicio, nombre
    FROM Dim_Servicio
    LIMIT {LIMITE}
"""


def extraer(consultar: Callable[[str], list[dict]] = query_pinot) -> dict[str, list[dict]]:
    return {
        "versiones": consultar(CONSULTA_VERSIONES),
        "servicios": consultar(CONSULTA_SERVICIOS),
    }


def _momento(valor: Any) -> datetime | None:
    if valor is None or valor == "" or valor == 0:
        return None
    if isinstance(valor, datetime):
        dt = valor.replace(tzinfo=None)
        return None if dt.year <= 1970 and dt.month == 1 and dt.day == 1 else dt
    if isinstance(valor, (int, float)):
        if valor <= 0:
            return None
        dt = a_datetime(int(valor))
        if dt is None or (dt.year <= 1970 and dt.month == 1 and dt.day == 1):
            return None
        return dt
    return None


def construir(
    datos: Mapping[str, Iterable[Mapping[str, Any]]], ahora: datetime
) -> list[dict]:
    carga = ahora.strftime(FORMATO)
    nombres = {
        int(s["id_servicio"]): (s.get("nombre") or None)
        for s in datos.get("servicios", [])
        if s.get("id_servicio") is not None
    }
    filas = []
    for v in datos.get("versiones", []):
        sid = int(v["id_servicio"])
        filas.append({
            "idversion": int(v["idversion"]),
            "id_servicio": sid,
            "servicio": nombres.get(sid),
            "version": str(v.get("version") or ""),
            "estado": str(v.get("estado") or ""),
            "fecha_publicacion": texto_fecha(_momento(v.get("fecha_publicacion"))),
            "fecha_retiro": texto_fecha(_momento(v.get("fecha_retiro"))),
            "version_carga": carga,
        })
    return filas
