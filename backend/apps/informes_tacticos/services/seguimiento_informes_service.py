from __future__ import annotations

from apps.informes_tacticos.periodo import Periodo
from core.repositories.informes_tacticos.seguimiento_repository import SeguimientoRepository


class SeguimientoInformesService:
    def __init__(self, repository: SeguimientoRepository | None = None):
        self.repository = repository or SeguimientoRepository()

    def tiempo_asignado_cerrado(self, periodo: Periodo) -> list[dict]:
        return self.repository.tiempo_asignado_cerrado(periodo.desde_ms, periodo.hasta_ms)

    def cierres_forzados(self, periodo: Periodo) -> list[dict]:
        return self.repository.cierres_forzados(periodo.desde_ms, periodo.hasta_ms, periodo.datetrunc_unit)

    def abortos_perdidas(self, periodo: Periodo) -> list[dict]:
        return self.repository.abortos_perdidas(periodo.desde_ms, periodo.hasta_ms)
