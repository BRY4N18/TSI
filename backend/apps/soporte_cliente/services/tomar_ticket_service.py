"""RF-TIC-002 paso 1 (CU-O92) — agente toma el ticket."""

from __future__ import annotations

from apps.soporte_cliente.domain_constants import (
    ESTADO_ABIERTO,
    ESTADO_EN_PROGRESO,
    ESTADO_REABIERTO,
)
from core.repositories.soporte.historial_ticket_repository import HistorialTicketRepository
from core.repositories.soporte.reclamo_repository import ReclamoRepository

_ESTADOS_TOMABLES = {ESTADO_ABIERTO, ESTADO_REABIERTO}


class TomarTicketService:
    def __init__(
        self,
        reclamo_repo: ReclamoRepository | None = None,
        historial_repo: HistorialTicketRepository | None = None,
    ):
        self.reclamo_repo = reclamo_repo or ReclamoRepository()
        self.historial_repo = historial_repo or HistorialTicketRepository()

    def tomar(self, id_reclamo: int, *, id_agente_asignado: int) -> dict:
        reclamo = self.reclamo_repo.find_by_id(id_reclamo)
        if not reclamo:
            raise LookupError(f"Ticket {id_reclamo} no encontrado")
        estado_anterior = reclamo["estado"]
        if estado_anterior not in _ESTADOS_TOMABLES:
            raise ValueError(f"El ticket no puede tomarse desde el estado {estado_anterior}")

        actualizado = self.reclamo_repo.update(
            id_reclamo,
            {"id_agente_asignado": id_agente_asignado, "estado": ESTADO_EN_PROGRESO},
        )
        self.historial_repo.append(
            id_reclamo=id_reclamo,
            tipo_accion="asignacion_agente",
            idusuario=id_agente_asignado,
            estado_anterior=estado_anterior,
            estado_nuevo=ESTADO_EN_PROGRESO,
        )
        return {
            **actualizado,
            "estado_anterior": estado_anterior,
            "estado_nuevo": ESTADO_EN_PROGRESO,
            "agente_asignado": id_agente_asignado,
        }
