"""CU-O54 — registrar unidad de emergencia individual."""

from __future__ import annotations

from typing import Any

from core.repositories.red_operativa.unidad_emergencia_repository import (
    UnidadEmergenciaRepository,
)

TIPOS_PROPIEDAD = {"Propia", "Externa"}
TIPOS_UNIDAD = {"Ambulancia", "Grúa", "Patrulla", "Bomberos", "Defensa Civil"}


class RegistroUnidadService:
    def __init__(self, unidad_repo: UnidadEmergenciaRepository | None = None):
        self.unidad_repo = unidad_repo or UnidadEmergenciaRepository()

    def registrar(self, data: dict[str, Any]) -> dict[str, Any]:
        self._validar(data)
        if self.unidad_repo.find_by_placa_activa(data["placa"]):
            raise ValueError(f"Ya existe una unidad activa con placa {data['placa']}")
        if not self.unidad_repo.condado_exists(data["idcondado"]):
            raise LookupError(f"idcondado {data['idcondado']} no existe")
        return self.unidad_repo.create(data)

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
