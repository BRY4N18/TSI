"""Read-only accidente checks for evidencia preconditions."""

from __future__ import annotations

from typing import Any

from apps.accidentes.domain_constants import ESTADO_CERRADO, ESTADO_DESCARTADO
from core.pinot.client import PinotClient
from core.repositories.accidentes.estado_accidente_repository import (
    EstadoAccidenteRepository,
)

ESTADOS_INACTIVOS = frozenset({ESTADO_CERRADO, ESTADO_DESCARTADO})


class AccidenteReadRepository:
    def __init__(
        self,
        pinot: PinotClient | None = None,
        estado_repo: EstadoAccidenteRepository | None = None,
    ):
        self.pinot = pinot or PinotClient()
        self.estado_repo = estado_repo or EstadoAccidenteRepository(pinot=self.pinot)

    def find_by_id(self, idaccidente: str) -> dict[str, Any] | None:
        rows = self.pinot.query(
            "SELECT * FROM Fact_Accidente WHERE idaccidente = %(idaccidente)s LIMIT 1",
            {"idaccidente": idaccidente},
        )
        return rows[0] if rows else None

    def get_current_estado(self, idaccidente: str) -> str | None:
        return self.estado_repo.get_current_estado(idaccidente)

    def is_caso_activo(self, idaccidente: str) -> bool:
        accidente = self.find_by_id(idaccidente)
        if not accidente or not accidente.get("activo", True):
            return False
        estado = self.get_current_estado(idaccidente)
        if estado and estado in ESTADOS_INACTIVOS:
            return False
        return True
