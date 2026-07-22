"""RF-TIC-002 paso 4 (CU-O92) — escalado manual a nivel superior."""

from __future__ import annotations

from apps.soporte_cliente.domain_constants import ESTADO_ESCALADO
from core.repositories.soporte.historial_ticket_repository import HistorialTicketRepository
from core.repositories.soporte.reclamo_repository import ReclamoRepository

NIVELES_ESCALADO = {"desarrollador_apis", "director_tecnologico"}


class EscalarTicketService:
    def __init__(
        self,
        reclamo_repo: ReclamoRepository | None = None,
        historial_repo: HistorialTicketRepository | None = None,
    ):
        self.reclamo_repo = reclamo_repo or ReclamoRepository()
        self.historial_repo = historial_repo or HistorialTicketRepository()

    def escalar(
        self,
        id_reclamo: int,
        *,
        id_rol_escalar: str,
        id_agente_asignado: int,
        mensaje: str | None = None,
        idusuario: int | None = None,
    ) -> dict:
        if id_rol_escalar not in NIVELES_ESCALADO:
            raise ValueError(f"id_rol_escalar inválido: {id_rol_escalar}")
        reclamo = self.reclamo_repo.find_by_id(id_reclamo)
        if not reclamo:
            raise LookupError(f"Ticket {id_reclamo} no encontrado")
        estado_anterior = reclamo["estado"]

        actualizado = self.reclamo_repo.update(
            id_reclamo,
            {"estado": ESTADO_ESCALADO, "id_agente_asignado": id_agente_asignado},
        )
        self.historial_repo.append(
            id_reclamo=id_reclamo,
            tipo_accion="escalado_manual",
            mensaje=mensaje,
            idusuario=idusuario,
            estado_anterior=estado_anterior,
            estado_nuevo=ESTADO_ESCALADO,
        )
        return {
            **actualizado,
            "estado_anterior": estado_anterior,
            "estado_nuevo": ESTADO_ESCALADO,
            "agente_asignado": id_agente_asignado,
        }
