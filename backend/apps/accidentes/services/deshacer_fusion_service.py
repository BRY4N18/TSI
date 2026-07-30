"""CU-O41 deshacer fusión (reversión rápida / snackbar)."""

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


class DeshacerFusionService:
    def __init__(
        self,
        accidente_repo: AccidenteRepository | None = None,
        estado_repo: EstadoAccidenteRepository | None = None,
        audit: AuditAccidenteService | None = None,
    ):
        self.accidente_repo = accidente_repo or AccidenteRepository()
        self.estado_repo = estado_repo or EstadoAccidenteRepository()
        self.audit = audit or AuditAccidenteService()

    def _estado_previo(self, idaccidente: str) -> str:
        history = self.estado_repo.get_history(idaccidente)
        # penúltimo estado antes de FUSIONADO
        for row in reversed(history[:-1] if history else []):
            estado = row.get("estado")
            if estado in {ESTADO_BORRADOR, ESTADO_REPORTADO}:
                return str(estado)
        return ESTADO_BORRADOR

    def deshacer(self, *, idaccidente_duplicado: str, idusuario: int) -> dict:
        current = self.estado_repo.get_current_estado(idaccidente_duplicado)
        if current != ESTADO_FUSIONADO:
            raise ConflictError("Solo se puede deshacer un caso en FUSIONADO")
        previo = self._estado_previo(idaccidente_duplicado)
        self.accidente_repo.update(
            idaccidente_duplicado,
            {"idaccidenteorigen": None, "activo": True},
        )
        self.estado_repo.append_estado(
            idaccidente=idaccidente_duplicado,
            estado=previo,
            idusuario=idusuario,
            motivo="Deshacer fusión (snackbar)",
        )
        self.audit.log_action(
            action="deshacer_fusion",
            user_id=idusuario,
            idaccidente=idaccidente_duplicado,
            extra={"estado_restaurado": previo},
        )
        return {
            "message": f"Fusión revertida; caso restaurado a {previo}",
            "idaccidente": idaccidente_duplicado,
            "estado": previo,
        }
