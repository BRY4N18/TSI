"""RF-TIC-006 / RF-TIC-002 paso 7 (CU-O92) — confirmación de cierre y auto-cierre."""

from __future__ import annotations

from datetime import datetime, timezone

from apps.soporte_cliente.domain_constants import (
    CIERRE_AUTOMATICO_DIAS,
    ESTADO_CERRADO,
    ESTADO_RESUELTO,
)
from core.repositories.soporte.historial_ticket_repository import HistorialTicketRepository
from core.repositories.soporte.reclamo_repository import ReclamoRepository


class ConfirmarCierreService:
    def __init__(
        self,
        reclamo_repo: ReclamoRepository | None = None,
        historial_repo: HistorialTicketRepository | None = None,
    ):
        self.reclamo_repo = reclamo_repo or ReclamoRepository()
        self.historial_repo = historial_repo or HistorialTicketRepository()

    def confirmar(self, id_reclamo: int, *, idusuario: int | None = None) -> dict:
        reclamo = self.reclamo_repo.find_by_id(id_reclamo)
        if not reclamo:
            raise LookupError(f"Ticket {id_reclamo} no encontrado")
        if reclamo["estado"] != ESTADO_RESUELTO:
            raise ValueError("El ticket no está en Resuelto")

        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        actualizado = self.reclamo_repo.update(
            id_reclamo,
            {
                "estado": ESTADO_CERRADO,
                "cierreconfirmadocliente": True,
                "fechahoraconfirmacioncierre": now_ms,
            },
        )
        self.historial_repo.append(
            id_reclamo=id_reclamo,
            tipo_accion="cierre_confirmado",
            idusuario=idusuario,
            estado_anterior=ESTADO_RESUELTO,
            estado_nuevo=ESTADO_CERRADO,
        )
        return {
            **actualizado,
            "estado_anterior": ESTADO_RESUELTO,
            "estado_nuevo": ESTADO_CERRADO,
            "agente_asignado": actualizado.get("id_agente_asignado"),
        }

    def cerrar_automaticamente_vencidos(self) -> list[dict]:
        """RN-TIC-004 — cierra tickets en Resuelto sin confirmación tras 5 días.

        Se ejecuta como parte del mismo ciclo que `MonitoreoSLAService` (único
        job periódico del módulo) — ver `jobs/monitoreo_sla_job.py`.
        """
        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        umbral = now_ms - CIERRE_AUTOMATICO_DIAS * 24 * 60 * 60 * 1000
        resueltos = self.reclamo_repo.list(idestadosoporte=ESTADO_RESUELTO, limit=10_000)
        cerrados = []
        for reclamo in resueltos:
            if reclamo.get("fecha_actualizacion", 0) <= umbral:
                actualizado = self.reclamo_repo.update(
                    reclamo["id_reclamo"],
                    {"estado": ESTADO_CERRADO, "cierreconfirmadocliente": False},
                )
                self.historial_repo.append(
                    id_reclamo=reclamo["id_reclamo"],
                    tipo_accion="cierre_automatico_por_vencimiento",
                    estado_anterior=ESTADO_RESUELTO,
                    estado_nuevo=ESTADO_CERRADO,
                )
                cerrados.append(actualizado)
        return cerrados
