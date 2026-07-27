"""CU-O58 — dar de baja y reactivar unidad (solo del Proveedor dueño)."""

from __future__ import annotations

from typing import Any

from apps.red_operativa.services.proveedor_access_service import ProveedorAccessService
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
        access: ProveedorAccessService | None = None,
    ):
        self.unidad_repo = unidad_repo or UnidadEmergenciaRepository()
        self.baja_repo = baja_repo or BajaUnidadRepository()
        self.despacho_repo = despacho_repo or DespachoActivoReadRepository()
        self.access = access or ProveedorAccessService()

    def dar_de_baja(
        self,
        idunidademergencia: int,
        *,
        motivo: str,
        idusuario: int,
        roles: list[str],
        forzar: bool = False,
    ) -> dict[str, Any]:
        unidad = self.unidad_repo.find_by_id(idunidademergencia)
        self.access.require_unidad_propia(user_id=idusuario, roles=roles, unidad=unidad)

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

    def reactivar(
        self,
        idunidademergencia: int,
        *,
        user_id: int,
        roles: list[str],
    ) -> dict[str, Any]:
        unidad = self.unidad_repo.find_by_id(idunidademergencia)
        self.access.require_unidad_propia(user_id=user_id, roles=roles, unidad=unidad)

        conflicto = self.unidad_repo.find_by_placa_activa(unidad["placa"])
        if conflicto and conflicto["idunidademergencia"] != idunidademergencia:
            raise ValueError(f"Ya existe otra unidad activa con placa {unidad['placa']}")

        return self.unidad_repo.update(idunidademergencia, {"activo": True})
