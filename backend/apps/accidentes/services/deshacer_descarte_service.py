"""CU-O32 deshacer descarte (reversión rápida / snackbar)."""

from __future__ import annotations

from apps.accidentes.domain_constants import ESTADO_BORRADOR, ESTADO_DESCARTADO
from apps.accidentes.services.audit_accidente_service import AuditAccidenteService
from apps.accidentes.services.confirmar_reporte_service import ConflictError
from core.repositories.accidentes.accidente_repository import AccidenteRepository
from core.repositories.accidentes.estado_accidente_repository import (
    EstadoAccidenteRepository,
)


class DeshacerDescarteService:
    def __init__(
        self,
        accidente_repo: AccidenteRepository | None = None,
        estado_repo: EstadoAccidenteRepository | None = None,
        audit: AuditAccidenteService | None = None,
    ):
        self.accidente_repo = accidente_repo or AccidenteRepository()
        self.estado_repo = estado_repo or EstadoAccidenteRepository()
        self.audit = audit or AuditAccidenteService()

    def deshacer(self, *, idaccidente: str, idusuario: int) -> dict:
        current = self.estado_repo.get_current_estado(idaccidente)
        if current != ESTADO_DESCARTADO:
            raise ConflictError("Solo se puede deshacer un caso en DESCARTADO")
        self.accidente_repo.update(idaccidente, {"activo": True})
        self.estado_repo.append_estado(
            idaccidente=idaccidente,
            estado=ESTADO_BORRADOR,
            idusuario=idusuario,
            motivo="Deshacer descarte (snackbar)",
        )
        self.audit.log_action(
            action="deshacer_descarte",
            user_id=idusuario,
            idaccidente=idaccidente,
        )
        return {
            "message": "Descarte revertido; caso restaurado a BORRADOR",
            "idaccidente": idaccidente,
            "estado": ESTADO_BORRADOR,
        }
