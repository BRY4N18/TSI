"""`dim_sla_config`: vigencias **tal como vienen del origen**.

⚠️ **No usa `versionado.py`.** Ese módulo construye historia comparando el
estado actual con el vigente; aquí la historia ya existe y es real. Aplicarlo
produciría versiones marcadas como no reales cuando sí lo son.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Iterable, Mapping

from lib.hechos.comun import FORMATO, a_datetime, texto_fecha
from lib.pinot_http_client import query_pinot

LIMITE = 10_000

CONSULTA = f"""
    SELECT idslaconfig, idplan, tipoincidencia, prioridad, activo,
           tiemporespuestamax, tiemporesolucionmax,
           fechavigenciadesde, fechavigenciahasta
    FROM Dim_SLAConfig
    LIMIT {LIMITE}
"""


def extraer(consultar: Callable[[str], list[dict]] = query_pinot) -> list[dict]:
    return consultar(CONSULTA)


def _entero(valor: Any) -> int | None:
    if valor is None or valor == "":
        return None
    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


def _momento(valor: Any) -> datetime | None:
    if valor is None or valor == "" or valor == 0:
        return None
    if isinstance(valor, datetime):
        return valor.replace(tzinfo=None)
    return a_datetime(int(valor)) if isinstance(valor, (int, float)) else a_datetime(valor)


def construir(filas_origen: Iterable[Mapping[str, Any]], ahora: datetime) -> list[dict]:
    version = ahora.strftime(FORMATO)
    filas = []
    for f in filas_origen:
        desde = _momento(f.get("fechavigenciadesde"))
        if desde is None:
            continue
        hasta = _momento(f.get("fechavigenciahasta"))
        filas.append({
            "idslaconfig": int(f["idslaconfig"]),
            "idplan": int(f["idplan"]),
            "tipo_incidencia": (f.get("tipoincidencia") or "").strip(),
            "prioridad": (f.get("prioridad") or "").strip(),
            "segundos_respuesta_max": _entero(f.get("tiemporespuestamax")) or 0,
            "segundos_resolucion_max": _entero(f.get("tiemporesolucionmax")) or 0,
            "valido_desde": texto_fecha(desde),
            "valido_hasta": texto_fecha(hasta),
            "es_vigente": 1 if hasta is None else 0,
            "version": version,
        })
    return filas
