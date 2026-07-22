"""CU-O62 — Despublicación automática por pérdida total de cobertura.

Servicio idempotente e invocable manualmente o por un job externo (cron).
**Sin disparador automático conectado**: RN-REGON-005 documenta que no existe
FK entre Dim_UnidadEmergencia y Dim_RegionOperativa, por lo que el conteo de
unidades activas de una región no puede resolverse de forma confiable a nivel
de esquema (ver plan.md Complexity Tracking, research.md Decision 4).

El registro de la transición no tiene actor humano (RF-REGON-004.2):
idusuario nunca se incluye en la respuesta ni se persiste en esta operación,
porque no existe tabla de historial donde insertar esa marca — el cambio es
solo el UPDATE de estadoregion.
"""

from __future__ import annotations

from typing import Any

from core.repositories.red_operativa.region_operativa_repository import (
    RegionOperativaRepository,
)

ESTADO_DESPUBLICADA = "Despublicada"
ESTADOS_ORIGEN_VALIDOS = ("Producción", "En_Alerta")


class DespublicacionAutomaticaService:
    def __init__(self, region_repo: RegionOperativaRepository | None = None):
        self.region_repo = region_repo or RegionOperativaRepository()

    def ejecutar(self, idregionoperativa: int) -> dict[str, Any]:
        region = self.region_repo.find_by_id(idregionoperativa)
        if not region:
            raise LookupError("Región no encontrada")
        if region["estadoregion"] not in ESTADOS_ORIGEN_VALIDOS:
            raise ValueError(
                "Solo se puede despublicar automáticamente una región en "
                "'Producción' o 'En_Alerta'"
            )
        updated = self.region_repo.update(idregionoperativa, {"estadoregion": ESTADO_DESPUBLICADA})
        return {"idregionoperativa": idregionoperativa, "estadoregion": updated["estadoregion"]}
