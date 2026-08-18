"""`hecho_accion_ticket`: transacción, **sin mensaje ni nota interna**."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Iterable, Mapping

from lib.hechos.comun import FORMATO, a_datetime, texto_fecha
from lib.pinot_http_client import query_pinot

LIMITE = 500_000

ACCIONES_ESCALADO = frozenset({"escalado_manual", "escalado_automatico_sla"})
ACCION_ESCALADO_AUTO = "escalado_automatico_sla"

#: ⚠️ `mensaje` y `es_nota_interna` no se piden: si no viajan, no pueden colarse.
CONSULTA = f"""
    SELECT id_historial, id_reclamo, tipo_accion, idusuario,
           estado_anterior, estado_nuevo, fecha_accion
    FROM Fact_Historial_Ticket
    LIMIT {LIMITE}
"""

CONSULTA_TICKETS = f"""
    SELECT id_reclamo, idcliente, id_agente_asignado
    FROM Fact_Reclamo
    LIMIT {LIMITE}
"""


def extraer(consultar: Callable[[str], list[dict]] = query_pinot) -> dict[str, list[dict]]:
    return {
        "historial": consultar(CONSULTA),
        "tickets": consultar(CONSULTA_TICKETS),
    }


def _momento(valor: Any) -> datetime | None:
    if valor is None or valor == "" or valor == 0:
        return None
    if isinstance(valor, datetime):
        return valor.replace(tzinfo=None)
    if isinstance(valor, (int, float)):
        if valor <= 0:
            return None
        return a_datetime(int(valor))
    texto = str(valor).strip()
    if not texto or texto.startswith("1970-01-01"):
        return None
    try:
        return datetime.fromisoformat(texto.replace("Z", "").split(".")[0])
    except ValueError:
        return None


def _entero(valor: Any) -> int | None:
    if valor is None or valor == "":
        return None
    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


def construir(datos: Mapping[str, Iterable[Mapping[str, Any]]], ahora: datetime) -> list[dict]:
    marca = ahora.strftime(FORMATO)
    tickets = {
        int(t["id_reclamo"]): t
        for t in datos.get("tickets", [])
        if t.get("id_reclamo") is not None
    }
    filas = []
    for h in datos.get("historial", []):
        momento = _momento(h.get("fecha_accion"))
        if momento is None:
            continue
        id_historial = _entero(h.get("id_historial"))
        id_reclamo = _entero(h.get("id_reclamo"))
        if id_historial is None or id_reclamo is None:
            continue
        tipo = (h.get("tipo_accion") or "").strip() or "desconocido"
        anterior = (h.get("estado_anterior") or None) or None
        nuevo = (h.get("estado_nuevo") or None) or None
        ticket = tickets.get(id_reclamo, {})
        filas.append({
            "id_historial": id_historial,
            "fecha": momento.date().isoformat(),
            "fechahora": texto_fecha(momento),
            "id_reclamo": id_reclamo,
            "idcliente": _entero(ticket.get("idcliente")),
            "idagente": _entero(h.get("idusuario")) or _entero(ticket.get("id_agente_asignado")),
            "tipo_accion": tipo,
            "es_escalado": 1 if tipo in ACCIONES_ESCALADO else 0,
            "es_escalado_automatico": 1 if tipo == ACCION_ESCALADO_AUTO else 0,
            "estado_anterior": anterior,
            "estado_nuevo": nuevo,
            "es_cambio_efectivo": 1 if anterior != nuevo else 0,
            "cargado_en": marca,
        })
    return filas
