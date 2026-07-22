"""CU-O58 — dar de baja y reactivar unidad de emergencia."""

from __future__ import annotations

from typing import Any

from core.repositories.red_operativa.baja_unidad_repository import BajaUnidadRepository
from core.repositories.red_operativa.despacho_activo_read_repository import (
    DespachoActivoReadRepository,
)
from core.repositories.red_operativa.unidad_emergencia_repository import (
    UnidadEmergenciaRepository,
)

TIPO_BAJA_NORMAL = "Normal"
TIPO_BAJA_FORZADA = "Forzada_con_reasignación"


class BajaUnidadService:
    def __init__(
        self,
        unidad_repo: UnidadEmergenciaRepository | None = None,
        baja_repo: BajaUnidadRepository | None = None,
        despacho_repo: DespachoActivoReadRepository | None = None,
    ):
        self.unidad_repo = unidad_repo or UnidadEmergenciaRepository()
        self.baja_repo = baja_repo or BajaUnidadRepository()
        self.despacho_repo = despacho_repo or DespachoActivoReadRepository()

    def dar_de_baja(
        self,
        idunidademergencia: int,
        *,
        motivo: str,
        idusuario: int,
        forzar: bool = False,
    ) -> dict[str, Any]:
        unidad = self.unidad_repo.find_by_id(idunidademergencia)
        if not unidad:
            raise LookupError("Unidad no encontrada")

        despacho_activo = self.despacho_repo.find_despacho_activo(idunidademergencia)
        if despacho_activo and not forzar:
            raise ValueError(
                "La unidad tiene un despacho activo; se requiere forzar la baja explícitamente"
            )

        self.baja_repo.create(
            {
                "idunidademergencia": idunidademergencia,
                "idusuario": idusuario,
                "idaccidente": despacho_activo["idaccidente"] if despacho_activo else None,
                "motivo": motivo,
                "tipobaja": TIPO_BAJA_FORZADA if despacho_activo else TIPO_BAJA_NORMAL,
            }
        )
        self.unidad_repo.update(idunidademergencia, {"activo": False})
        return {"idunidademergencia": idunidademergencia, "activo": False}

    def reactivar(self, idunidademergencia: int) -> dict[str, Any]:
        unidad = self.unidad_repo.find_by_id(idunidademergencia)
        if not unidad:
            raise LookupError("Unidad no encontrada")

        conflicto = self.unidad_repo.find_by_placa_activa(unidad["placa"])
        if conflicto and conflicto["idunidademergencia"] != idunidademergencia:
            raise ValueError(f"Ya existe otra unidad activa con placa {unidad['placa']}")

        return self.unidad_repo.update(idunidademergencia, {"activo": True})
