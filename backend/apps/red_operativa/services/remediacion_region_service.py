"""CU-O60 — Gestionar resultado fallido de validación y remediación.

Camino negativo de CU-O55: el reintento de validación es simplemente una
nueva ejecución de ValidacionRegionService (no cubierto aquí). Este servicio
cubre la consulta de historial y el rechazo definitivo.
"""

from __future__ import annotations

from typing import Any

from core.repositories.red_operativa.region_operativa_repository import (
    ESTADO_EN_VALIDACION,
    RegionOperativaRepository,
)
from core.repositories.red_operativa.validacion_region_repository import (
    ValidacionRegionRepository,
)


class RemediacionRegionService:
    def __init__(
        self,
        region_repo: RegionOperativaRepository | None = None,
        validacion_repo: ValidacionRegionRepository | None = None,
    ):
        self.region_repo = region_repo or RegionOperativaRepository()
        self.validacion_repo = validacion_repo or ValidacionRegionRepository()

    def historial(self, idregionoperativa: int) -> list[dict[str, Any]]:
        return self.validacion_repo.list_by_region(idregionoperativa)

    def rechazo_definitivo(self, idregionoperativa: int) -> dict[str, Any]:
        region = self.region_repo.find_by_id(idregionoperativa)
        if not region:
            raise LookupError("Región no encontrada")
        if region["estadoregion"] != ESTADO_EN_VALIDACION:
            raise ValueError(
                "Solo se puede marcar rechazo definitivo sobre una región en En_Validación"
            )
        self.region_repo.update(idregionoperativa, {"activo": False})
        return {"idregionoperativa": idregionoperativa, "activo": False}
