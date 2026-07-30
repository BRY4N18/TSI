"""CU-O61 — Re-evaluar/despublicar una región habilitada (Producción).

Regla de continuidad (RF-REGON-003, RNF-REGON-002): la despublicación nunca
cancela casos de emergencia activos — solo bloquea casos nuevos.

El motivo se persiste como fila append-only en Dim_ValidacionRegion
(resultado='Reevaluacion') porque no hay tabla de historial de transiciones.
"""

from __future__ import annotations

from typing import Any

from core.repositories.red_operativa.accidente_activo_read_repository import (
    AccidenteActivoReadRepository,
)
from core.repositories.red_operativa.region_operativa_repository import (
    RegionOperativaRepository,
)
from core.repositories.red_operativa.validacion_region_repository import (
    ValidacionRegionRepository,
)

ESTADO_PRODUCCION = "Producción"
ESTADO_EN_ALERTA = "En_Alerta"
ESTADO_DESPUBLICADA = "Despublicada"
ESTADOS_ORIGEN_VALIDOS = (ESTADO_PRODUCCION, ESTADO_EN_ALERTA)
ESTADOS_DESTINO_VALIDOS = (ESTADO_EN_ALERTA, ESTADO_DESPUBLICADA)
RESULTADO_REEVALUACION = "Reevaluacion"


class ReevaluacionRegionService:
    def __init__(
        self,
        region_repo: RegionOperativaRepository | None = None,
        accidente_repo: AccidenteActivoReadRepository | None = None,
        validacion_repo: ValidacionRegionRepository | None = None,
    ):
        self.region_repo = region_repo or RegionOperativaRepository()
        self.accidente_repo = accidente_repo or AccidenteActivoReadRepository()
        self.validacion_repo = validacion_repo or ValidacionRegionRepository()

    def reevaluar(
        self,
        idregionoperativa: int,
        *,
        estadoregion_nuevo: str,
        motivo: str,
        idusuario: int,
    ) -> dict[str, Any]:
        if estadoregion_nuevo not in ESTADOS_DESTINO_VALIDOS:
            raise KeyError("estadoregion debe ser 'En_Alerta' o 'Despublicada'")
        if not str(motivo).strip():
            raise ValueError("motivo es requerido")

        region = self.region_repo.find_by_id(idregionoperativa)
        if not region:
            raise LookupError("Región no encontrada")
        if region["estadoregion"] not in ESTADOS_ORIGEN_VALIDOS:
            raise ValueError(
                "Solo se puede re-evaluar una región en 'Producción' o 'En_Alerta'"
            )

        self.accidente_repo.existen_casos_activos(idregionoperativa)

        updated = self.region_repo.update(idregionoperativa, {"estadoregion": estadoregion_nuevo})
        self.validacion_repo.create(
            {
                "idregionoperativa": idregionoperativa,
                "idusuario": idusuario,
                "resultado": RESULTADO_REEVALUACION,
                "motivo": f"{estadoregion_nuevo}: {motivo.strip()}",
            }
        )
        return {
            "idregionoperativa": idregionoperativa,
            "estadoregion": updated["estadoregion"],
            "motivo": motivo.strip(),
        }
