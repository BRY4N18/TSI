"""CU-O58 descartar caso."""

from __future__ import annotations

from apps.accidentes.domain_constants import (
    ESTADO_BORRADOR,
    ESTADO_DESCARTADO,
    ESTADO_REPORTADO,
)
from apps.accidentes.services.audit_accidente_service import AuditAccidenteService
from apps.accidentes.services.confirmar_reporte_service import ConflictError
from core.repositories.accidentes.accidente_repository import AccidenteRepository
from core.repositories.accidentes.estado_accidente_repository import (
    EstadoAccidenteRepository,
)
from core.repositories.despacho.despacho_repository import DespachoRepository


class DescartarCasoService:
    def __init__(
        self,
        accidente_repo: AccidenteRepository | None = None,
        estado_repo: EstadoAccidenteRepository | None = None,
        audit: AuditAccidenteService | None = None,
        despacho_repo: DespachoRepository | None = None,
    ):
        self.accidente_repo = accidente_repo or AccidenteRepository()
        self.estado_repo = estado_repo or EstadoAccidenteRepository()
        self.audit = audit or AuditAccidenteService()
        self.despacho_repo = despacho_repo or DespachoRepository()

    def descartar(self, *, idaccidente: str, idusuario: int, motivo: str | None = None) -> dict:
        # SRS §3.6.1: descartar una falsa alarma "solo es posible mientras no exista
        # ningún despacho creado". La guarda anterior exigía BORRADOR, que es una
        # condición distinta y más estricta: como el registro se autoconfirma a
        # REPORTADO cuando no hay advertencias, una falsa alarma limpia **no se podía
        # descartar nunca**, aunque no se hubiera despachado a nadie.
        current = self.estado_repo.get_current_estado(idaccidente)
        if current not in (ESTADO_BORRADOR, ESTADO_REPORTADO):
            raise ConflictError(
                f"No se puede descartar un caso en {current}; solo antes de despachar"
            )
        if self.despacho_repo.list_by_accidente(idaccidente):
            raise ConflictError(
                "El caso ya tiene despachos creados; no se puede descartar"
            )
        # RF-REG-007.4 / SRS 3.6.1: el motivo es opcional, no obligatorio
        # (corrección 2026-08-08 — el código lo exigía, contradiciendo SRS,
        # spec y contrato OpenAPI).
        self.accidente_repo.update(idaccidente, {"activo": False})
        self.estado_repo.append_estado(
            idaccidente=idaccidente,
            estado=ESTADO_DESCARTADO,
            idusuario=idusuario,
            motivo=motivo,
        )
        self.audit.log_action(
            action="descartar",
            user_id=idusuario,
            idaccidente=idaccidente,
            extra={"motivo": motivo},
        )
        return {
            "message": "Caso descartado exitosamente",
            "idaccidente": idaccidente,
            "estado": ESTADO_DESCARTADO,
        }
