"""Catálogo geográfico en cascada — servicio wrapper (ver repository)."""

from core.repositories.accidentes.ubicacion_catalogo_repository import (
    UbicacionCatalogoRepository,
)


class UbicacionCatalogoService:
    def __init__(self, repo: UbicacionCatalogoRepository | None = None):
        self.repo = repo or UbicacionCatalogoRepository()

    def listar_paises(self) -> list[dict]:
        return self.repo.listar_paises()

    def listar_estados(self, idpais: int) -> list[dict]:
        return self.repo.listar_estados(idpais)

    def listar_condados(self, idestado: int) -> list[dict]:
        return self.repo.listar_condados(idestado)

    def listar_ciudades(self, idcondado: int) -> list[dict]:
        return self.repo.listar_ciudades(idcondado)

    def listar_calles(self, idciudad: int) -> list[dict]:
        return self.repo.listar_calles(idciudad)
