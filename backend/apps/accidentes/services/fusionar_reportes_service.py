"""CU-O41 fusionar reportes."""

from __future__ import annotations

from apps.accidentes.domain_constants import (
    ESTADO_BORRADOR,
    ESTADO_FUSIONADO,
    ESTADO_REPORTADO,
)
from apps.accidentes.services.audit_accidente_service import AuditAccidenteService
from apps.accidentes.services.confirmar_reporte_service import ConflictError
from core.repositories.accidentes.accidente_repository import AccidenteRepository
from core.repositories.accidentes.estado_accidente_repository import (
    EstadoAccidenteRepository,
)


class FusionarReportesService:
    ALLOWED = {ESTADO_BORRADOR, ESTADO_REPORTADO}

    def __init__(
        self,
        accidente_repo: AccidenteRepository | None = None,
        estado_repo: EstadoAccidenteRepository | None = None,
        audit: AuditAccidenteService | None = None,
    ):
        self.accidente_repo = accidente_repo or AccidenteRepository()
        self.estado_repo = estado_repo or EstadoAccidenteRepository()
        self.audit = audit or AuditAccidenteService()

    def fusionar(
        self,
        *,
        idaccidente_duplicado: str,
        idaccidente_principal: str,
        idusuario: int,
        confirmacion: bool,
    ) -> dict:
        if not confirmacion:
            raise ValueError("Confirmación requerida")
        for aid in (idaccidente_duplicado, idaccidente_principal):
            estado = self.estado_repo.get_current_estado(aid)
            if estado not in self.ALLOWED:
                raise ConflictError("Fusión no permitida para el estado actual")

        self.accidente_repo.update(
            idaccidente_duplicado,
            {"idaccidenteorigen": idaccidente_principal, "activo": False},
        )
        self.estado_repo.append_estado(
            idaccidente=idaccidente_duplicado,
            estado=ESTADO_FUSIONADO,
            idusuario=idusuario,
        )
        self.audit.log_action(
            action="fusionar",
            user_id=idusuario,
            idaccidente=idaccidente_duplicado,
            extra={"idaccidente_principal": idaccidente_principal},
        )
        return {
            "message": "Reportes fusionados exitosamente",
            "idaccidente_duplicado": idaccidente_duplicado,
            "idaccidente_principal": idaccidente_principal,
            "estado_duplicado": ESTADO_FUSIONADO,
        }
