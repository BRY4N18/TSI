"""Servicios de catálogo para registro / escalar (CU-O21, CU-O40)."""

from __future__ import annotations

from core.repositories.accidentes.catalogo_registro_repository import (
    CatalogoRegistroRepository,
)
from core.repositories.despacho.unidad_emergencia_repository import (
    UnidadEmergenciaRepository,
)


class CatalogoRegistroService:
    def __init__(
        self,
        registro_repo: CatalogoRegistroRepository | None = None,
        unidad_repo: UnidadEmergenciaRepository | None = None,
    ):
        self.registro_repo = registro_repo or CatalogoRegistroRepository()
        self.unidad_repo = unidad_repo or UnidadEmergenciaRepository()

    def listar_tipos_reportado(self) -> list[dict]:
        return self.registro_repo.listar_tipos_reportado()

    def listar_referencias_estacion(self) -> list[dict]:
        return self.registro_repo.listar_referencias_estacion()

    def listar_unidades_emergencia(self) -> list[dict]:
        unidades = self.unidad_repo.list_active(limit=200)
        return [
            {
                "id": u["idunidademergencia"],
                "nombre": u.get("unidademergencia") or f"Unidad #{u['idunidademergencia']}",
            }
            for u in unidades
        ]
