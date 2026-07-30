"""RF-EVI-008 — elementos físicos en sitio."""

from __future__ import annotations

from typing import Any

from core.audit.evidencia_service import AuditEvidenciaService
from core.repositories.accidentes.elemento_fisico_repository import ElementoFisicoRepository
from core.repositories.evidencia.accidente_read_repository import AccidenteReadRepository
from core.repositories.evidencia.catalogo_enriquecimiento_repository import (
    CatalogoEnriquecimientoRepository,
)


class EnriquecimientoElementoFisicoService:
    def __init__(
        self,
        accidente_repo: AccidenteReadRepository | None = None,
        fisico_repo: ElementoFisicoRepository | None = None,
        catalogo_repo: CatalogoEnriquecimientoRepository | None = None,
        audit: AuditEvidenciaService | None = None,
    ):
        self.accidente_repo = accidente_repo or AccidenteReadRepository()
        self.fisico_repo = fisico_repo or ElementoFisicoRepository()
        self.catalogo_repo = catalogo_repo or CatalogoEnriquecimientoRepository()
        self.audit = audit or AuditEvidenciaService()

    def _enrich(self, row: dict[str, Any]) -> dict[str, Any]:
        cat = self.catalogo_repo.find_elemento_fisico(int(row["idelementofisico"]))
        return {
            **row,
            "elementofisico": (cat or {}).get("elementofisico"),
        }

    def listar(self, idaccidente: str) -> list[dict[str, Any]]:
        if not self.accidente_repo.find_by_id(idaccidente):
            raise LookupError("Accidente no encontrado")
        return [self._enrich(r) for r in self.fisico_repo.list_activos_by_accidente(idaccidente)]

    def agregar(
        self, *, idaccidente: str, idelementofisico: int, idusuario: int
    ) -> dict[str, Any]:
        if not self.accidente_repo.find_by_id(idaccidente):
            raise LookupError("Accidente no encontrado")
        if not self.accidente_repo.is_caso_activo(idaccidente):
            raise ValueError("El caso no está activo para enriquecer")
        if not self.catalogo_repo.find_elemento_fisico(idelementofisico):
            raise ValueError("idelementofisico inválido")
        record = self.fisico_repo.upsert(
            idaccidente=idaccidente,
            idelementofisico=idelementofisico,
            idusuario=idusuario,
        )
        self.audit.log_enriquecer_elemento_fisico(
            user_id=idusuario,
            idaccidente=idaccidente,
            idelementofisico=idelementofisico,
        )
        return self._enrich(record)

    def desactivar(
        self, *, idaccidente: str, idelementosfisicosaccidente: int, idusuario: int
    ) -> dict[str, Any]:
        current = self.fisico_repo.find_by_id(idelementosfisicosaccidente)
        if not current or current.get("idaccidente") != idaccidente:
            raise LookupError("Elemento físico no encontrado")
        if not self.accidente_repo.is_caso_activo(idaccidente):
            raise ValueError("El caso no está activo para enriquecer")
        record = self.fisico_repo.soft_delete(
            idelementosfisicosaccidente=idelementosfisicosaccidente,
            idusuario=idusuario,
        )
        assert record is not None
        return self._enrich(record)
