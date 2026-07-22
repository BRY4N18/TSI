"""CU-O55 — Ejecutar protocolo de validación de operatividad de una región.

Revisión manual (sin checklist técnico automatizado, ver Clarifications del
spec) — el sistema solo persiste el resultado declarado por el Administrador
o el Director Tecnológico en Dim_ValidacionRegion, y transiciona
Dim_RegionOperativa.estadoregion cuando el resultado es 'Aprobada'.
"""

from __future__ import annotations

from typing import Any

from core.repositories.red_operativa.region_operativa_repository import (
    ESTADO_EN_VALIDACION,
    RegionOperativaRepository,
)
from core.repositories.red_operativa.validacion_region_repository import (
    RESULTADO_APROBADA,
    RESULTADO_RECHAZADA,
    ValidacionRegionRepository,
)

ESTADO_PRODUCCION = "Producción"


class ValidacionRegionService:
    def __init__(
        self,
        region_repo: RegionOperativaRepository | None = None,
        validacion_repo: ValidacionRegionRepository | None = None,
    ):
        self.region_repo = region_repo or RegionOperativaRepository()
        self.validacion_repo = validacion_repo or ValidacionRegionRepository()

    def ejecutar(self, data: dict[str, Any], *, idusuario: int) -> dict[str, Any]:
        resultado = data.get("resultado")
        if resultado not in (RESULTADO_APROBADA, RESULTADO_RECHAZADA):
            raise ValueError("resultado debe ser 'Aprobada' o 'Rechazada'")
        if resultado == RESULTADO_RECHAZADA and not data.get("motivo"):
            raise ValueError("motivo es requerido cuando resultado='Rechazada'")

        idregionoperativa = data.get("idregionoperativa")
        if idregionoperativa is None:
            region = self.region_repo.create(
                {
                    "idestado": data["idestado"],
                    "nombreregion": data["nombreregion"],
                    "estadoregion": ESTADO_EN_VALIDACION,
                }
            )
            idregionoperativa = region["idregionoperativa"]
        else:
            region = self.region_repo.find_by_id(idregionoperativa)
            if not region:
                raise LookupError("Región no encontrada")

        validacion = self.validacion_repo.create(
            {
                "idregionoperativa": idregionoperativa,
                "idusuario": idusuario,
                "resultado": resultado,
                "motivo": data.get("motivo"),
            }
        )

        if resultado == RESULTADO_APROBADA:
            region = self.region_repo.update(idregionoperativa, {"estadoregion": ESTADO_PRODUCCION})

        return {
            "idregionoperativa": idregionoperativa,
            "idvalidacionregion": validacion["idvalidacionregion"],
            "resultado": resultado,
            "estadoregion_actual": region["estadoregion"],
        }
