"""Listado de Dim_Servicio para selects de registro de ticket."""

from __future__ import annotations

from core.repositories.soporte.servicio_catalogo_repository import (
    ServicioCatalogoRepository,
)


class CatalogoServicioService:
    def __init__(self, repo: ServicioCatalogoRepository | None = None):
        self.repo = repo or ServicioCatalogoRepository()

    def listar(self) -> list[dict]:
        return self.repo.listar_activos()
