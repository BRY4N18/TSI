"""RF-TIC-005 (CU-O97) — reapertura de ticket cerrado con renovación de SLA.

research.md Decision 8 (clarificación Session 2026-07-21): reutiliza
`AsignacionSLAService` para recalcular el SLA contra la configuración vigente
actual, en vez de conservar los valores originales.
"""

from __future__ import annotations

from apps.soporte_cliente.domain_constants import ESTADO_CERRADO, ESTADO_REABIERTO
from apps.soporte_cliente.services.asignacion_sla_service import AsignacionSLAService
from core.repositories.soporte.archivo_adjunto_reclamo_repository import (
    ArchivoAdjuntoReclamoRepository,
)
from core.repositories.soporte.historial_ticket_repository import HistorialTicketRepository
from core.repositories.soporte.reclamo_repository import ReclamoRepository
from core.storage.blob_storage_service import BlobStorageService


class ReabrirTicketService:
    def __init__(
        self,
        reclamo_repo: ReclamoRepository | None = None,
        historial_repo: HistorialTicketRepository | None = None,
        adjunto_repo: ArchivoAdjuntoReclamoRepository | None = None,
        asignacion_sla_service: AsignacionSLAService | None = None,
        blob_storage: BlobStorageService | None = None,
    ):
        self.reclamo_repo = reclamo_repo or ReclamoRepository()
        self.historial_repo = historial_repo or HistorialTicketRepository()
        self.adjunto_repo = adjunto_repo or ArchivoAdjuntoReclamoRepository()
        self.asignacion_sla_service = asignacion_sla_service or AsignacionSLAService()
        self.blob_storage = blob_storage or BlobStorageService()

    def _subir_adjuntos(self, id_reclamo: int, archivos: list[tuple[bytes, str]]) -> None:
        for content, content_type in archivos:
            file_key = self.blob_storage.generate_file_key()
            url = self.blob_storage.upload(
                idaccidente=f"tickets/{id_reclamo}",
                file_key=file_key,
                content=content,
                content_type=content_type,
            )
            self.adjunto_repo.append(id_reclamo=id_reclamo, urlarchivo=url)

    def reabrir(
        self,
        id_reclamo: int,
        *,
        idusuario: int | None = None,
        motivo: str | None = None,
        adjuntos: list[tuple[bytes, str]] | None = None,
    ) -> dict:
        reclamo = self.reclamo_repo.find_by_id(id_reclamo)
        if not reclamo:
            raise LookupError(f"Ticket {id_reclamo} no encontrado")
        if reclamo["estado"] != ESTADO_CERRADO:
            raise ValueError("Solo un ticket Cerrado puede reabrirse")

        sla = self.asignacion_sla_service.asignar(
            idcliente=reclamo["idcliente"],
            tipo_incidencia=reclamo["tipo_incidencia"],
            prioridad=reclamo["prioridad"],
        )
        cambios = {"estado": ESTADO_REABIERTO, **(sla or {})}
        actualizado = self.reclamo_repo.update(id_reclamo, cambios)

        self.historial_repo.append(
            id_reclamo=id_reclamo,
            tipo_accion="reapertura",
            mensaje=motivo,
            idusuario=idusuario,
            estado_anterior=ESTADO_CERRADO,
            estado_nuevo=ESTADO_REABIERTO,
        )
        if adjuntos:
            self._subir_adjuntos(id_reclamo, adjuntos)

        return {
            **actualizado,
            "estado_anterior": ESTADO_CERRADO,
            "estado_nuevo": ESTADO_REABIERTO,
            "agente_asignado": actualizado.get("id_agente_asignado"),
        }
