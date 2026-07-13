"""CU-O38 — coordinación de despacho múltiple."""

from __future__ import annotations

from typing import Any

from apps.despacho.services.asignacion_manual_service import AsignacionManualService
from core.repositories.despacho.despacho_repository import DespachoRepository


class CoordinacionMultipleService:
    def __init__(
        self,
        asignacion_manual: AsignacionManualService | None = None,
        despacho_repo: DespachoRepository | None = None,
    ):
        self.manual = asignacion_manual or AsignacionManualService()
        self.despachos = despacho_repo or DespachoRepository()

    def coordinar(
        self,
        *,
        idaccidente: str,
        idunidademergencia: int,
        idusuario: int,
    ) -> dict[str, Any]:
        activos = self.despachos.list_by_accidente(idaccidente, activo=True)
        if not activos:
            raise ValueError("Caso sin despacho activo previo")
        if any(int(d["idunidademergencia"]) == idunidademergencia for d in activos):
            raise ValueError("Unidad ya asignada al caso")
        result = self.manual.asignar(
            idaccidente=idaccidente,
            idunidademergencia=idunidademergencia,
            idusuario=idusuario,
        )
        return {
            **result,
            "message": "Despacho múltiple coordinado",
        }
