"""RF-TIC-004 (CU-O89) — monitoreo y escalado automático de SLA.

Clarificación Session 2026-07-21: `sla_primera_respuesta` y `sla_resolucion`
se vigilan de forma independiente — cualquiera de los dos que cruce el umbral
dispara la alerta/escalado.
"""

from __future__ import annotations

from datetime import datetime, timezone

from apps.soporte_cliente.domain_constants import (
    ESTADO_CERRADO,
    ESTADO_ESCALADO,
    ESTADO_RESUELTO,
    SLA_EN_RIESGO,
    SLA_INCUMPLIDO,
    SLA_UMBRAL_RIESGO_PCT,
)
from core.repositories.soporte.historial_ticket_repository import HistorialTicketRepository
from core.repositories.soporte.reclamo_repository import ReclamoRepository
from core.repositories.soporte.supervisor_soporte_repository import SupervisorSoporteRepository

_ESTADOS_NO_VIGILADOS = {ESTADO_CERRADO, ESTADO_RESUELTO}


class MonitoreoSLAService:
    def __init__(
        self,
        reclamo_repo: ReclamoRepository | None = None,
        historial_repo: HistorialTicketRepository | None = None,
        supervisor_repo: SupervisorSoporteRepository | None = None,
    ):
        self.reclamo_repo = reclamo_repo or ReclamoRepository()
        self.historial_repo = historial_repo or HistorialTicketRepository()
        self.supervisor_repo = supervisor_repo or SupervisorSoporteRepository()

    @staticmethod
    def _pct_consumido(fechahora: int, deadline: int, now_ms: int) -> float:
        total = deadline - fechahora
        if total <= 0:
            return 1.0
        return (now_ms - fechahora) / total

    def ejecutar_ciclo(self) -> dict[str, int]:
        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        tickets = self.reclamo_repo.list(limit=10_000)
        escalados = 0
        en_riesgo = 0

        for ticket in tickets:
            if ticket["estado"] in _ESTADOS_NO_VIGILADOS:
                continue
            # Sin compromiso no hay nada que vigilar, y son DOS casos distintos
            # que antes se confundian en este mismo silencio: el ticket sin
            # clasificar (que tiene su propio estado y se ve) y el clasificado
            # sin regla aplicable, que se marca `sla_status='sin compromiso'`
            # precisamente para que no parezca un ticket cronometrado.
            if ticket.get("idslaconfig") is None:
                continue
            fechahora = ticket["fechahora"]
            plazos = [p for p in (ticket.get("sla_primera_respuesta"), ticket.get("sla_resolucion")) if p is not None]
            if not plazos:
                continue
            pcts = [self._pct_consumido(fechahora, p, now_ms) for p in plazos]
            pct_max = max(pcts)

            if pct_max >= 1.0:
                self._escalar_por_incumplimiento(ticket)
                escalados += 1
            elif pct_max >= SLA_UMBRAL_RIESGO_PCT and ticket.get("sla_status") != SLA_EN_RIESGO:
                self._marcar_en_riesgo(ticket)
                en_riesgo += 1

        return {"escalados": escalados, "en_riesgo": en_riesgo}

    def _marcar_en_riesgo(self, ticket: dict) -> None:
        self.reclamo_repo.update(ticket["id_reclamo"], {"sla_status": SLA_EN_RIESGO})
        self.historial_repo.append(
            id_reclamo=ticket["id_reclamo"],
            tipo_accion="alerta_sla_riesgo",
        )

    def _escalar_por_incumplimiento(self, ticket: dict) -> None:
        estado_anterior = ticket["estado"]
        supervisor_idusuario = self.supervisor_repo.get_supervisor_idusuario()
        self.reclamo_repo.update(
            ticket["id_reclamo"],
            {
                "sla_status": SLA_INCUMPLIDO,
                "estado": ESTADO_ESCALADO,
                "id_agente_asignado": supervisor_idusuario,
            },
        )
        # SIN `idusuario`: R-03 y §3.7.1 del SRS piden que el escalado automatico
        # quede "registrado como accion del sistema, NO de una persona". Estampar
        # aqui al supervisor hacia que la bitacora dijera que lo escalo el, cuando
        # el es el destino, no el autor: el supervisor va en `id_agente_asignado`
        # y en ningun otro sitio. Sin esto no se puede distinguir una decision
        # humana de una automatica, que es justo lo que R-03 protege.
        self.historial_repo.append(
            id_reclamo=ticket["id_reclamo"],
            tipo_accion="escalado_automatico_sla",
            estado_anterior=estado_anterior,
            estado_nuevo=ESTADO_ESCALADO,
        )
