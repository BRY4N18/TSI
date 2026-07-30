"""RF-EVI-007 — upsert clima/período en sitio."""

from __future__ import annotations

from typing import Any

from core.audit.evidencia_service import AuditEvidenciaService
from core.repositories.accidentes.elemento_climatico_repository import (
    ElementoClimaticoRepository,
)
from core.repositories.evidencia.accidente_read_repository import AccidenteReadRepository
from core.repositories.evidencia.catalogo_enriquecimiento_repository import (
    CatalogoEnriquecimientoRepository,
)


class EnriquecimientoClimaService:
    def __init__(
        self,
        accidente_repo: AccidenteReadRepository | None = None,
        climatico_repo: ElementoClimaticoRepository | None = None,
        catalogo_repo: CatalogoEnriquecimientoRepository | None = None,
        audit: AuditEvidenciaService | None = None,
    ):
        self.accidente_repo = accidente_repo or AccidenteReadRepository()
        self.climatico_repo = climatico_repo or ElementoClimaticoRepository()
        self.catalogo_repo = catalogo_repo or CatalogoEnriquecimientoRepository()
        self.audit = audit or AuditEvidenciaService()

    def upsert(
        self,
        *,
        idaccidente: str,
        idusuario: int,
        idperiododia: int | None,
        idestadoclima: int | None,
    ) -> dict[str, Any]:
        if idperiododia is None and idestadoclima is None:
            raise ValueError("Se requiere idperiododia o idestadoclima")
        if not self.accidente_repo.find_by_id(idaccidente):
            raise LookupError("Accidente no encontrado")
        if not self.accidente_repo.is_caso_activo(idaccidente):
            raise ValueError("El caso no está activo para enriquecer")
        if idperiododia is not None and not self.catalogo_repo.find_periodo(idperiododia):
            raise ValueError("idperiododia inválido")
        if idestadoclima is not None and not self.catalogo_repo.find_estado_clima(idestadoclima):
            raise ValueError("idestadoclima inválido")

        record = self.climatico_repo.upsert(
            idaccidente=idaccidente,
            idperiododia=idperiododia,
            idestadoclima=idestadoclima,
            idusuario=idusuario,
        )
        self.audit.log_enriquecer_clima(user_id=idusuario, idaccidente=idaccidente)
        return record
