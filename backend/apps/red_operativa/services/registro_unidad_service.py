"""CU-O54 — registrar unidad de emergencia individual (actor Proveedor)."""

from __future__ import annotations

from typing import Any

from apps.red_operativa.services.proveedor_access_service import (
    ProveedorAccessError,
    ProveedorAccessService,
)
from core.repositories.red_operativa.unidad_emergencia_repository import (
    UnidadEmergenciaRepository,
)

TIPOS_PROPIEDAD = {"Propia", "Externa"}
TIPOS_UNIDAD = {"Ambulancia", "Grúa", "Patrulla", "Bomberos", "Defensa Civil"}


class RegistroUnidadService:
    def __init__(
        self,
        unidad_repo: UnidadEmergenciaRepository | None = None,
        access: ProveedorAccessService | None = None,
    ):
        self.unidad_repo = unidad_repo or UnidadEmergenciaRepository()
        self.access = access or ProveedorAccessService()

    def registrar(
        self,
        data: dict[str, Any],
        *,
        user_id: int,
        roles: list[str],
    ) -> dict[str, Any]:
        cliente = self.access.resolve_cliente_activo(user_id=user_id, roles=roles)
        payload = dict(data)
        payload.pop("idcliente", None)
        payload["idcliente"] = cliente["idcliente"]
        if not payload.get("tipopropiedad"):
            payload["tipopropiedad"] = "Externa"
        self._validar(payload)
        if self.unidad_repo.find_by_placa_activa(payload["placa"]):
            raise ValueError(f"Ya existe una unidad activa con placa {payload['placa']}")
        if not self.unidad_repo.condado_exists(payload["idcondado"]):
            raise LookupError(f"idcondado {payload['idcondado']} no existe")
        return self.unidad_repo.create(payload)

    def _validar(self, data: dict[str, Any]) -> None:
        if not data.get("idcliente"):
            raise KeyError("idcliente es requerido")
        if data.get("tipopropiedad") not in TIPOS_PROPIEDAD:
            raise KeyError("tipopropiedad inválido")
        if not data.get("placa"):
            raise KeyError("placa es requerida")
        if not data.get("idcondado"):
            raise KeyError("idcondado es requerido")
        if not data.get("unidademergencia"):
            raise KeyError("unidademergencia es requerido")
        if data.get("tipounidademergencia") not in TIPOS_UNIDAD:
            raise KeyError("tipounidademergencia inválido")
        if data["tipopropiedad"] == "Externa" and not data.get("contactoproveedor"):
            raise KeyError("contactoproveedor es requerido para unidades Externa")
