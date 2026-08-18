"""`dim_partner`: catálogo sin contacto técnico.

Normaliza el texto `'null'` de `plan_api` a ausente (decisión #15).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Iterable, Mapping

from lib.hechos.comun import FORMATO, a_datetime, texto_fecha
from lib.pinot_http_client import query_pinot

LIMITE = 50_000

#: Sin `contacto_tecnico_nombre` ni `contacto_tecnico_gmail`.
CONSULTA = f"""
    SELECT idpartner, idcliente, nombrepartner, planapi,
           limitellamadasmes, limitellamadasminuto, activo,
           fecha_suspension, sandbox_activado, sandbox_expiracion
    FROM Dim_Partner
    LIMIT {LIMITE}
"""

CENTINELA_CUPO = -1


def extraer(consultar: Callable[[str], list[dict]] = query_pinot) -> list[dict]:
    return consultar(CONSULTA)


def _plan(valor: Any) -> str | None:
    if valor is None:
        return None
    texto = str(valor).strip()
    if not texto or texto.lower() in {"null", "none"}:
        return None
    return texto


def _cupo(valor: Any) -> int | None:
    if valor is None or valor == "" or valor == CENTINELA_CUPO:
        return None
    try:
        n = int(valor)
    except (TypeError, ValueError):
        return None
    return None if n < 0 else n


def _momento(valor: Any) -> datetime | None:
    if valor is None or valor == "" or valor == 0:
        return None
    if isinstance(valor, datetime):
        return valor.replace(tzinfo=None)
    if isinstance(valor, (int, float)):
        if valor <= 0:
            return None
        return a_datetime(int(valor))
    return None


def construir(filas: Iterable[Mapping[str, Any]], ahora: datetime) -> list[dict]:
    version = ahora.strftime(FORMATO)
    out = []
    for f in filas:
        activo = f.get("activo") in (True, 1, "true", "1", "True")
        out.append({
            "idpartner": int(f["idpartner"]),
            "nombre_partner": (f.get("nombrepartner") or f.get("nombre_partner") or "").strip(),
            "idcliente": int(f["idcliente"]) if f.get("idcliente") not in (None, "") else None,
            "plan_api": _plan(f.get("planapi") if f.get("planapi") is not None else f.get("plan_api")),
            "limite_llamadas_mes": _cupo(f.get("limitellamadasmes")),
            "limite_llamadas_minuto": _cupo(f.get("limitellamadasminuto")),
            "estado": "activo" if activo else "suspendido",
            "fecha_suspension": texto_fecha(_momento(f.get("fecha_suspension"))),
            "sandbox_activado": texto_fecha(_momento(f.get("sandbox_activado"))),
            "sandbox_expiracion": texto_fecha(_momento(f.get("sandbox_expiracion"))),
            "version": version,
        })
    return out
