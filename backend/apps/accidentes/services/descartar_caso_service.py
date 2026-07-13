"""CU-O32 descartar caso."""

from __future__ import annotations

from apps.accidentes.domain_constants import ESTADO_BORRADOR, ESTADO_DESCARTADO
from apps.accidentes.services.audit_accidente_service import AuditAccidenteService
from apps.accidentes.services.confirmar_reporte_service import ConflictError
from core.repositories.accidentes.accidente_repository import AccidenteRepository
from core.repositories.accidentes.estado_accidente_repository import EstadoAccidenteRepository


class DescartarCasoService:
    def __init__(
        self,
        accidente_repo: AccidenteRepository | None = None,
        estado_repo: EstadoAccidenteRepository | None = None,
        audit: AuditAccidenteService | None = None,
    ):
        self.accidente_repo = accidente_repo or AccidenteRepository()
        self.estado_repo = estado_repo or EstadoAccidenteRepository()
        self.audit = audit or AuditAccidenteService()

    def descartar(self, *, idaccidente: str, idusuario: int, motivo: str | None = None) -> dict:
        current = self.estado_repo.get_current_estado(idaccidente)
        if current != ESTADO_BORRADOR:
            raise ConflictError("Solo se puede descartar en BORRADOR")
        self.accidente_repo.update(idaccidente, {"activo": False})
        self.estado_repo.append_estado(
            idaccidente=idaccidente, estado=ESTADO_DESCARTADO, idusuario=idusuario
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
