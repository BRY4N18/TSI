from __future__ import annotations

from apps.informes_tacticos.periodo import Periodo
from core.repositories.informes_tacticos.indice_calidad_repository import IndiceCalidadRepository
from core.repositories.informes_tacticos.perdida_senal_repository import PerdidaSenalRepository
from core.repositories.informes_tacticos.rendimiento_proveedor_repository import (
    RendimientoProveedorRepository,
)


class InformesCompuestosService:
    def __init__(
        self,
        perdida_senal_repository: PerdidaSenalRepository | None = None,
        indice_calidad_repository: IndiceCalidadRepository | None = None,
        rendimiento_proveedor_repository: RendimientoProveedorRepository | None = None,
    ):
        self.perdida_senal_repository = perdida_senal_repository or PerdidaSenalRepository()
        self.indice_calidad_repository = indice_calidad_repository or IndiceCalidadRepository()
        self.rendimiento_proveedor_repository = (
            rendimiento_proveedor_repository or RendimientoProveedorRepository()
        )

    def perdida_senal(self, periodo: Periodo) -> tuple[list[dict] | None, str | None]:
        return self.perdida_senal_repository.consultar(periodo.desde, periodo.hasta)

    def indice_calidad(self, periodo: Periodo) -> tuple[list[dict] | None, str | None]:
        return self.indice_calidad_repository.consultar(periodo.desde, periodo.hasta)

    def rendimiento_proveedor(self, periodo: Periodo) -> tuple[list[dict] | None, str | None]:
        return self.rendimiento_proveedor_repository.consultar(periodo.desde, periodo.hasta)
