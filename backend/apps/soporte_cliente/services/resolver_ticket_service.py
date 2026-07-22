"""RF-TIC-002 paso 5 (CU-O92) — resolución del ticket con recálculo de SLA."""

from __future__ import annotations

from datetime import datetime, timezone

from apps.soporte_cliente.domain_constants import (
    ESTADO_EN_PROGRESO,
    ESTADO_ESCALADO,
    ESTADO_RESUELTO,
    SLA_CUMPLIDO,
    SLA_INCUMPLIDO,
)
from core.repositories.soporte.historial_ticket_repository import HistorialTicketRepository
from core.repositories.soporte.reclamo_repository import ReclamoRepository

_ESTADOS_RESOLVIBLES = {ESTADO_EN_PROGRESO, ESTADO_ESCALADO}


class ResolverTicketService:
    def __init__(
        self,
        reclamo_repo: ReclamoRepository | None = None,
        historial_repo: HistorialTicketRepository | None = None,
    ):
        self.reclamo_repo = reclamo_repo or ReclamoRepository()
        self.historial_repo = historial_repo or HistorialTicketRepository()

    def resolver(self, id_reclamo: int, *, mensaje: str | None = None, idusuario: int | None = None) -> dict:
        reclamo = self.reclamo_repo.find_by_id(id_reclamo)
        if not reclamo:
            raise LookupError(f"Ticket {id_reclamo} no encontrado")
        estado_anterior = reclamo["estado"]
        if estado_anterior not in _ESTADOS_RESOLVIBLES:
            raise ValueError(f"El ticket no puede resolverse desde el estado {estado_anterior}")
        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        tiempo_solucion = now_ms - reclamo["fechahora"]

        sla_resolucion = reclamo.get("sla_resolucion")
        if sla_resolucion is not None:
            sla_status = SLA_CUMPLIDO if now_ms <= sla_resolucion else SLA_INCUMPLIDO
        else:
            sla_status = reclamo.get("sla_status")

        actualizado = self.reclamo_repo.update(
            id_reclamo,
            {
                "estado": ESTADO_RESUELTO,
                "tiempo_solucion": tiempo_solucion,
                "sla_status": sla_status,
            },
        )
        self.historial_repo.append(
            id_reclamo=id_reclamo,
            tipo_accion="resolucion",
            mensaje=mensaje,
            idusuario=idusuario,
            estado_anterior=estado_anterior,
            estado_nuevo=ESTADO_RESUELTO,
        )
        return {
            **actualizado,
            "estado_anterior": estado_anterior,
            "estado_nuevo": ESTADO_RESUELTO,
            "agente_asignado": actualizado.get("id_agente_asignado"),
        }
