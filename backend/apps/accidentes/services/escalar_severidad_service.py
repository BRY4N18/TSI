"""CU-O40 escalar severidad."""

from __future__ import annotations

from typing import Any

from apps.accidentes.domain_constants import ESTADO_ASIGNADO, ESTADO_EN_ATENCION
from apps.accidentes.services.audit_accidente_service import AuditAccidenteService
from apps.accidentes.services.confirmar_reporte_service import ConflictError
from core.repositories.accidentes.accidente_repository import AccidenteRepository
from core.repositories.accidentes.despacho_read_repository import DespachoReadRepository
from core.repositories.accidentes.estado_accidente_repository import (
    EstadoAccidenteRepository,
)
from core.repositories.accidentes.nota_accidente_repository import (
    NotaAccidenteRepository,
)


class EscalarSeveridadService:
    ALLOWED_ESTADOS = {ESTADO_ASIGNADO, ESTADO_EN_ATENCION}

    def __init__(
        self,
        accidente_repo: AccidenteRepository | None = None,
        estado_repo: EstadoAccidenteRepository | None = None,
        despacho_repo: DespachoReadRepository | None = None,
        nota_repo: NotaAccidenteRepository | None = None,
        audit: AuditAccidenteService | None = None,
    ):
        self.accidente_repo = accidente_repo or AccidenteRepository()
        self.estado_repo = estado_repo or EstadoAccidenteRepository()
        self.despacho_repo = despacho_repo or DespachoReadRepository()
        self.nota_repo = nota_repo or NotaAccidenteRepository()
        self.audit = audit or AuditAccidenteService()

    def escalar(self, *, idaccidente: str, data: dict[str, Any], idusuario: int) -> dict:
        estado = self.estado_repo.get_current_estado(idaccidente)
        if estado not in self.ALLOWED_ESTADOS:
            raise ConflictError("Estado no permite escalamiento")
        if not self.despacho_repo.has_active_confirmed(idaccidente):
            raise ConflictError("Sin despacho activo confirmado")

        current = self.accidente_repo.find_by_id(idaccidente)
        if not current:
            raise LookupError("Accidente no encontrado")

        updates: dict[str, Any] = {"idseveridad": data["idseveridad"]}
        for field in ("numheridos", "numfallecidos"):
            if field in data and data[field] is not None:
                old = current.get(field) or 0
                if data[field] < old:
                    raise ValueError(f"{field} solo puede incrementarse")
                updates[field] = data[field]
        if data.get("descripcion"):
            updates["descripcion"] = data["descripcion"]

        self.accidente_repo.update(idaccidente, updates)
        self.nota_repo.create_escalamiento(
            idaccidente=idaccidente,
            idusuario=idusuario,
            nota=data["nota"],
        )
        self.audit.log_action(action="escalar", user_id=idusuario, idaccidente=idaccidente)

        return {
            "message": "Severidad escalada exitosamente",
            "idaccidente": idaccidente,
            "idseveridad": data["idseveridad"],
            "estado": estado,
        }
