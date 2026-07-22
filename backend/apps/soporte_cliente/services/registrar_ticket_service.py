"""RF-TIC-001 (CU-O91) — registrar ticket con clasificación automática y SLA."""

from __future__ import annotations

from apps.soporte_cliente.domain_constants import (
    ESTADO_ABIERTO,
    ESTADO_PENDIENTE_DE_CLASIFICACION,
)
from apps.soporte_cliente.services.asignacion_sla_service import AsignacionSLAService
from apps.soporte_cliente.services.clasificacion_automatica_service import (
    ClasificacionAutomaticaService,
)
from core.repositories.soporte.archivo_adjunto_reclamo_repository import (
    ArchivoAdjuntoReclamoRepository,
)
from core.repositories.soporte.historial_ticket_repository import HistorialTicketRepository
from core.repositories.soporte.reclamo_repository import ReclamoRepository
from core.storage.blob_storage_service import BlobStorageService


class RegistrarTicketService:
    """Nota de alcance: los adjuntos reutilizan `BlobStorageService` (mismo backend
    que evidencia fotográfica), por lo que heredan su restricción a JPEG/PNG —
    cubre el caso principal (capturas de pantalla); otros formatos quedan fuera
    de este ciclo."""

    def __init__(
        self,
        reclamo_repo: ReclamoRepository | None = None,
        historial_repo: HistorialTicketRepository | None = None,
        adjunto_repo: ArchivoAdjuntoReclamoRepository | None = None,
        clasificacion_service: ClasificacionAutomaticaService | None = None,
        asignacion_sla_service: AsignacionSLAService | None = None,
        blob_storage: BlobStorageService | None = None,
    ):
        self.reclamo_repo = reclamo_repo or ReclamoRepository()
        self.historial_repo = historial_repo or HistorialTicketRepository()
        self.adjunto_repo = adjunto_repo or ArchivoAdjuntoReclamoRepository()
        self.clasificacion_service = clasificacion_service or ClasificacionAutomaticaService()
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

    def registrar(
        self,
        *,
        idcliente: int,
        asunto: str,
        descripcion: str,
        tipo: str,
        idaccidente: str | None = None,
        idusuario: int | None = None,
        adjuntos: list[tuple[bytes, str]] | None = None,
    ) -> dict:
        clasificacion = self.clasificacion_service.clasificar(
            tipo=tipo, asunto=asunto, descripcion=descripcion, idaccidente=idaccidente
        )

        if clasificacion is None:
            reclamo = self.reclamo_repo.create(
                {
                    "idcliente": idcliente,
                    "asunto": asunto,
                    "descripcion": descripcion,
                    "tipo": tipo,
                    "tipo_incidencia": None,
                    "prioridad": None,
                    "estado": ESTADO_PENDIENTE_DE_CLASIFICACION,
                    "idslaconfig": None,
                    "sla_status": None,
                    "cierreconfirmadocliente": False,
                }
            )
        else:
            sla = self.asignacion_sla_service.asignar(
                idcliente=idcliente,
                tipo_incidencia=clasificacion["tipo_incidencia"],
                prioridad=clasificacion["prioridad"],
            )
            reclamo = self.reclamo_repo.create(
                {
                    "idcliente": idcliente,
                    "asunto": asunto,
                    "descripcion": descripcion,
                    "tipo": tipo,
                    "tipo_incidencia": clasificacion["tipo_incidencia"],
                    "prioridad": clasificacion["prioridad"],
                    "estado": ESTADO_ABIERTO,
                    "cierreconfirmadocliente": False,
                    "idslaconfig": None,
                    "sla_primera_respuesta": None,
                    "sla_resolucion": None,
                    "sla_status": None,
                    **(sla or {}),
                }
            )

        if adjuntos:
            self._subir_adjuntos(reclamo["id_reclamo"], adjuntos)

        self.historial_repo.append(
            id_reclamo=reclamo["id_reclamo"],
            tipo_accion="creacion",
            idusuario=idusuario,
            estado_nuevo=reclamo["estado"],
        )
        return reclamo

    def clasificar_manual(
        self,
        id_reclamo: int,
        *,
        tipo_incidencia: str,
        prioridad: str,
        idusuario: int | None = None,
    ) -> dict:
        """RF-TIC-001 paso 4 / RN-TIC-003 — clasificación manual arranca el SLA."""
        reclamo = self.reclamo_repo.find_by_id(id_reclamo)
        if not reclamo:
            raise LookupError(f"Ticket {id_reclamo} no encontrado")
        if reclamo["estado"] != ESTADO_PENDIENTE_DE_CLASIFICACION:
            raise ValueError("El ticket no está en Pendiente_de_clasificacion")

        sla = self.asignacion_sla_service.asignar(
            idcliente=reclamo["idcliente"],
            tipo_incidencia=tipo_incidencia,
            prioridad=prioridad,
        )
        actualizado = self.reclamo_repo.update(
            id_reclamo,
            {
                "tipo_incidencia": tipo_incidencia,
                "prioridad": prioridad,
                "estado": ESTADO_ABIERTO,
                **(sla or {}),
            },
        )
        self.historial_repo.append(
            id_reclamo=id_reclamo,
            tipo_accion="clasificacion_manual",
            idusuario=idusuario,
            estado_anterior=ESTADO_PENDIENTE_DE_CLASIFICACION,
            estado_nuevo=ESTADO_ABIERTO,
        )
        return actualizado
