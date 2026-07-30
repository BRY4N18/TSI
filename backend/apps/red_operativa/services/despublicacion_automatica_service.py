"""CU-O62 — Despublicación automática por pérdida total de cobertura.

Regla de cobertura (RN-REGON-005 resuelta):
  Dim_RegionOperativaEstadoRegion → Dim_Condado → Dim_UnidadEmergencia(activo).

Solo despublica si el conteo de unidades activas en esa cobertura es 0.
Invocable por Administrador o job/cron externo (POST .../despublicacion-automatica).
Sin actor humano en la respuesta (RF-REGON-004).
"""

from __future__ import annotations

from typing import Any

from core.repositories.red_operativa.cobertura_region_read_repository import (
    CoberturaRegionReadRepository,
)
from core.repositories.red_operativa.region_operativa_repository import (
    RegionOperativaRepository,
)

ESTADO_DESPUBLICADA = "Despublicada"
ESTADOS_ORIGEN_VALIDOS = ("Producción", "En_Alerta")


class DespublicacionAutomaticaService:
    def __init__(
        self,
        region_repo: RegionOperativaRepository | None = None,
        cobertura_repo: CoberturaRegionReadRepository | None = None,
    ):
        self.region_repo = region_repo or RegionOperativaRepository()
        self.cobertura_repo = cobertura_repo or CoberturaRegionReadRepository()

    def ejecutar(self, idregionoperativa: int) -> dict[str, Any]:
        region = self.region_repo.find_by_id(idregionoperativa)
        if not region:
            raise LookupError("Región no encontrada")
        if region["estadoregion"] not in ESTADOS_ORIGEN_VALIDOS:
            raise ValueError(
                "Solo se puede despublicar automáticamente una región en "
                "'Producción' o 'En_Alerta'"
            )
        activas = self.cobertura_repo.count_unidades_activas(idregionoperativa)
        if activas > 0:
            raise ValueError(
                f"La región aún tiene {activas} unidad(es) activa(s) en cobertura; "
                "no se puede despublicar automáticamente"
            )
        updated = self.region_repo.update(
            idregionoperativa, {"estadoregion": ESTADO_DESPUBLICADA}
        )
        return {
            "idregionoperativa": idregionoperativa,
            "estadoregion": updated["estadoregion"],
            "unidades_activas": 0,
        }
