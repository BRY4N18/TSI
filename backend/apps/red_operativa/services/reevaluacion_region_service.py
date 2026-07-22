"""CU-O61 — Re-evaluar/despublicar una región habilitada (Producción).

Regla de continuidad (RF-REGON-003, RNF-REGON-002): la despublicación nunca
cancela casos de emergencia activos — solo bloquea casos nuevos, verificación
que se ejecuta en tiempo real fuera de este servicio (en registro-accidente,
módulo Emergencias). Aquí solo se consulta AccidenteActivoReadRepository como
contexto informativo, sin bloquear la transición.
"""

from __future__ import annotations

from typing import Any

from core.repositories.red_operativa.accidente_activo_read_repository import (
    AccidenteActivoReadRepository,
)
from core.repositories.red_operativa.region_operativa_repository import (
    RegionOperativaRepository,
)

ESTADO_PRODUCCION = "Producción"
ESTADO_EN_ALERTA = "En_Alerta"
ESTADO_DESPUBLICADA = "Despublicada"
ESTADOS_ORIGEN_VALIDOS = (ESTADO_PRODUCCION, ESTADO_EN_ALERTA)
ESTADOS_DESTINO_VALIDOS = (ESTADO_EN_ALERTA, ESTADO_DESPUBLICADA)


class ReevaluacionRegionService:
    def __init__(
        self,
        region_repo: RegionOperativaRepository | None = None,
        accidente_repo: AccidenteActivoReadRepository | None = None,
    ):
        self.region_repo = region_repo or RegionOperativaRepository()
        self.accidente_repo = accidente_repo or AccidenteActivoReadRepository()

    def reevaluar(
        self, idregionoperativa: int, *, estadoregion_nuevo: str, motivo: str
    ) -> dict[str, Any]:
        if estadoregion_nuevo not in ESTADOS_DESTINO_VALIDOS:
            raise KeyError("estadoregion debe ser 'En_Alerta' o 'Despublicada'")

        region = self.region_repo.find_by_id(idregionoperativa)
        if not region:
            raise LookupError("Región no encontrada")
        if region["estadoregion"] not in ESTADOS_ORIGEN_VALIDOS:
            raise ValueError(
                "Solo se puede re-evaluar una región en 'Producción' o 'En_Alerta'"
            )

        # Informativo únicamente (RN-REGON-004): la despublicación nunca cancela
        # casos activos, por lo que su presencia no bloquea esta transición.
        self.accidente_repo.existen_casos_activos(idregionoperativa)

        updated = self.region_repo.update(idregionoperativa, {"estadoregion": estadoregion_nuevo})
        return {"idregionoperativa": idregionoperativa, "estadoregion": updated["estadoregion"]}
