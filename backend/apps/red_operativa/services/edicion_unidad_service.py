"""CU-O57 — editar unidad existente."""

from __future__ import annotations

from typing import Any

from core.repositories.red_operativa.despacho_activo_read_repository import (
    DespachoActivoReadRepository,
)
from core.repositories.red_operativa.unidad_emergencia_repository import (
    UnidadEmergenciaRepository,
)

CAMPOS_EDITABLES = {
    "tipopropiedad",
    "capacidad",
    "idcondado",
    "contactoproveedor",
    "unidademergencia",
    "tipounidademergencia",
    "latitud",
    "longitud",
}
CAMPOS_CRITICOS = {"tipopropiedad", "tipounidademergencia"}


class EdicionUnidadService:
    def __init__(
        self,
        unidad_repo: UnidadEmergenciaRepository | None = None,
        despacho_repo: DespachoActivoReadRepository | None = None,
    ):
        self.unidad_repo = unidad_repo or UnidadEmergenciaRepository()
        self.despacho_repo = despacho_repo or DespachoActivoReadRepository()

    def editar(
        self,
        idunidademergencia: int,
        data: dict[str, Any],
        *,
        confirmar_edicion_critica: bool = False,
    ) -> dict[str, Any] | None:
        cambios = {k: v for k, v in data.items() if k in CAMPOS_EDITABLES}
        if not cambios:
            raise KeyError("No hay campos editables en la solicitud")

        toca_campo_critico = bool(set(cambios) & CAMPOS_CRITICOS)
        if toca_campo_critico and not confirmar_edicion_critica:
            if self.despacho_repo.has_despacho_activo(idunidademergencia):
                raise ValueError(
                    "La unidad tiene un despacho activo; se requiere confirmación explícita"
                )

        return self.unidad_repo.update(idunidademergencia, cambios)
