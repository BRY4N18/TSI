"""CU-O57 — editar unidad existente (solo unidades del Proveedor)."""

from __future__ import annotations

from typing import Any

from apps.red_operativa.services.proveedor_access_service import (
    ProveedorAccessService,
)
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
        access: ProveedorAccessService | None = None,
    ):
        self.unidad_repo = unidad_repo or UnidadEmergenciaRepository()
        self.despacho_repo = despacho_repo or DespachoActivoReadRepository()
        self.access = access or ProveedorAccessService()

    def editar(
        self,
        idunidademergencia: int,
        data: dict[str, Any],
        *,
        user_id: int,
        roles: list[str],
        confirmar_edicion_critica: bool = False,
    ) -> dict[str, Any] | None:
        unidad = self.unidad_repo.find_by_id(idunidademergencia)
        self.access.require_unidad_propia(user_id=user_id, roles=roles, unidad=unidad)

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
