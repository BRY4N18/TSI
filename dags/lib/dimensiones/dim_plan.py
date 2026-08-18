"""`dim_plan`: catálogo de planes con límites **desplegados**.

El origen guarda `limites` y `severidades_desbloqueadas` como texto. Interpretarlo
en cada consulta repartiría esa lógica por el catálogo, y la primera que lo lea
distinto devolvería otra cifra para la misma pregunta (research D5).
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Callable, Iterable, Mapping

from lib.pinot_http_client import query_pinot

LIMITE = 10_000

CONSULTA = f"""
    SELECT idplan, nombre, precio, limites, nivel, periodicidad,
           severidades_desbloqueadas, carga_lote_habilitada,
           precio_excedente_llamada, activo
    FROM Dim_Plan
    LIMIT {LIMITE}
"""


def extraer(consultar: Callable[[str], list[dict]] = query_pinot) -> list[dict]:
    return consultar(CONSULTA)


def _json(valor: Any) -> Any:
    if valor is None or valor == "" or valor == "null":
        return None
    if isinstance(valor, (dict, list)):
        return valor
    try:
        return json.loads(valor)
    except (TypeError, json.JSONDecodeError, ValueError):
        return None


def _entero(valor: Any) -> int | None:
    if valor is None or valor == "":
        return None
    try:
        n = int(valor)
    except (TypeError, ValueError):
        return None
    return n


def _decimal(valor: Any) -> float | None:
    if valor is None or valor == "":
        return None
    try:
        n = float(valor)
    except (TypeError, ValueError):
        return None
    if n < 0:
        return None
    return n


def desplegar_limites(texto: Any) -> dict[str, int | None]:
    """Convierte el JSON de límites en columnas comparables.

    Claves del origen: `unidades_max`, `usuarios_max`, `api_calls_mes`,
    `api_calls_minuto`. Lo que no venga, queda ausente —nunca cero—.
    """
    datos = _json(texto)
    if not isinstance(datos, dict):
        datos = {}
    return {
        "limite_unidades": _entero(datos.get("unidades_max")),
        "limite_usuarios": _entero(datos.get("usuarios_max")),
        "limite_llamadas_mes": _entero(datos.get("api_calls_mes")),
        "limite_llamadas_minuto": _entero(datos.get("api_calls_minuto")),
    }


def desplegar_severidades(texto: Any) -> list[int]:
    datos = _json(texto)
    if not isinstance(datos, list):
        return []
    out: list[int] = []
    for item in datos:
        n = _entero(item)
        if n is not None:
            out.append(n)
    return out


def construir(filas_origen: Iterable[Mapping[str, Any]], ahora: datetime) -> list[dict]:
    version = ahora.strftime("%Y-%m-%d %H:%M:%S")
    filas = []
    for f in filas_origen:
        limites = desplegar_limites(f.get("limites"))
        filas.append({
            "idplan": int(f["idplan"]),
            "nombre": (f.get("nombre") or "").strip() or "",
            "nivel": (f.get("nivel") or None),
            "periodicidad": (f.get("periodicidad") or None),
            "precio_lista": _decimal(f.get("precio")),
            "precio_excedente_llamada": _decimal(f.get("precio_excedente_llamada")),
            **limites,
            "severidades_habilitadas": desplegar_severidades(f.get("severidades_desbloqueadas")),
            "carga_lote_habilitada": 1 if f.get("carga_lote_habilitada") in (True, 1, "true", "1") else 0,
            "es_activo": 1 if f.get("activo") in (True, 1, "true", "1") else 0,
            "version": version,
        })
    return filas
