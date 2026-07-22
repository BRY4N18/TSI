"""RF-TIC-007 — dashboard de soporte."""

from __future__ import annotations

from collections import Counter

from apps.soporte_cliente.domain_constants import (
    ESTADO_CERRADO,
    ESTADO_RESUELTO,
    SLA_EN_RIESGO,
    SLA_INCUMPLIDO,
)
from core.repositories.soporte.historial_ticket_repository import HistorialTicketRepository
from core.repositories.soporte.reclamo_repository import ReclamoRepository

_ESTADOS_RESUELTOS_O_CERRADOS = {ESTADO_RESUELTO, ESTADO_CERRADO}


class DashboardSoporteService:
    def __init__(
        self,
        reclamo_repo: ReclamoRepository | None = None,
        historial_repo: HistorialTicketRepository | None = None,
    ):
        self.reclamo_repo = reclamo_repo or ReclamoRepository()
        self.historial_repo = historial_repo or HistorialTicketRepository()

    def _tiempo_primera_respuesta_ms(self, ticket: dict) -> int | None:
        historial = self.historial_repo.list_by_ticket(ticket["id_reclamo"])
        primera = next((h for h in historial if h["tipo_accion"] == "asignacion_agente"), None)
        if not primera:
            return None
        return primera["fecha_accion"] - ticket["fechahora"]

    def _tasa_reapertura(self, tickets: list[dict]) -> float:
        cerrados_alguna_vez = [
            t for t in tickets if t["estado"] in (ESTADO_CERRADO,) or t.get("estado") == "Reabierto"
        ]
        if not cerrados_alguna_vez:
            return 0.0
        reabiertos = 0
        for t in tickets:
            historial = self.historial_repo.list_by_ticket(t["id_reclamo"])
            if any(h["tipo_accion"] == "reapertura" for h in historial):
                reabiertos += 1
        return reabiertos / len(cerrados_alguna_vez)

    def metricas(self) -> dict:
        tickets = self.reclamo_repo.list(limit=100_000)

        por_estado = dict(Counter(t["estado"] for t in tickets))
        por_prioridad = dict(Counter(t["prioridad"] for t in tickets if t.get("prioridad")))
        por_tipo_incidencia = dict(
            Counter(t["tipo_incidencia"] for t in tickets if t.get("tipo_incidencia"))
        )
        por_cliente = dict(Counter(t["idcliente"] for t in tickets))

        sla_en_riesgo = sum(1 for t in tickets if t.get("sla_status") == SLA_EN_RIESGO)
        sla_vencidos = sum(1 for t in tickets if t.get("sla_status") == SLA_INCUMPLIDO)

        resueltos_o_cerrados = [t for t in tickets if t["estado"] in _ESTADOS_RESUELTOS_O_CERRADOS]
        tiempos_resolucion = [
            t["tiempo_solucion"] for t in resueltos_o_cerrados if t.get("tiempo_solucion") is not None
        ]
        tiempo_promedio_resolucion_ms = (
            sum(tiempos_resolucion) / len(tiempos_resolucion) if tiempos_resolucion else None
        )

        tiempos_primera_respuesta = [
            v for v in (self._tiempo_primera_respuesta_ms(t) for t in tickets) if v is not None
        ]
        tiempo_promedio_primera_respuesta_ms = (
            sum(tiempos_primera_respuesta) / len(tiempos_primera_respuesta)
            if tiempos_primera_respuesta
            else None
        )

        return {
            "total_tickets": len(tickets),
            "por_estado": por_estado,
            "por_prioridad": por_prioridad,
            "por_tipo_incidencia": por_tipo_incidencia,
            "por_cliente": por_cliente,
            "sla_en_riesgo": sla_en_riesgo,
            "sla_vencidos": sla_vencidos,
            "tiempo_promedio_primera_respuesta_ms": tiempo_promedio_primera_respuesta_ms,
            "tiempo_promedio_resolucion_ms": tiempo_promedio_resolucion_ms,
            "tasa_reapertura": self._tasa_reapertura(tickets),
        }
