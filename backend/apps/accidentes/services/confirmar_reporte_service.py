"""RF-REG-010 confirmar BORRADOR → REPORTADO."""

from __future__ import annotations

from apps.accidentes.domain_constants import ESTADO_BORRADOR, ESTADO_REPORTADO
from apps.accidentes.services.audit_accidente_service import AuditAccidenteService
from core.repositories.accidentes.estado_accidente_repository import EstadoAccidenteRepository


class ConfirmarReporteService:
    def __init__(
        self,
        estado_repo: EstadoAccidenteRepository | None = None,
        audit: AuditAccidenteService | None = None,
    ):
        self.estado_repo = estado_repo or EstadoAccidenteRepository()
        self.audit = audit or AuditAccidenteService()

    def confirmar(self, *, idaccidente: str, idusuario: int, confirmacion: bool) -> dict:
        if not confirmacion:
            raise ValueError("Confirmación requerida")
        current = self.estado_repo.get_current_estado(idaccidente)
        if current != ESTADO_BORRADOR:
            raise ConflictError("Caso no está en BORRADOR")
        self.estado_repo.append_estado(
            idaccidente=idaccidente, estado=ESTADO_REPORTADO, idusuario=idusuario
        )
        self.audit.log_action(action="confirmar_reporte", user_id=idusuario, idaccidente=idaccidente)
        return {
            "message": "Caso confirmado y reportado",
            "idaccidente": idaccidente,
            "estado": ESTADO_REPORTADO,
        }


class ConflictError(Exception):
    pass
