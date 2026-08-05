from __future__ import annotations

from apps.informes_tacticos.periodo import Periodo
from core.repositories.informes_tacticos.despacho_repository import DespachoRepository


class DespachoInformesService:
    def __init__(self, repository: DespachoRepository | None = None):
        self.repository = repository or DespachoRepository()

    def asignacion_automatica_vs_manual(self, periodo: Periodo, idcondado: int | None = None) -> list[dict]:
        return self.repository.asignacion_automatica_vs_manual(periodo.desde_ms, periodo.hasta_ms, idcondado)

    def tiempo_reportado_confirmado(self, periodo: Periodo) -> dict:
        return self.repository.tiempo_reportado_confirmado(periodo.desde_ms, periodo.hasta_ms)

    def tiempo_respuesta_por_severidad(self, periodo: Periodo, idcondado: int | None = None) -> list[dict]:
        return self.repository.tiempo_respuesta_por_severidad(periodo.desde_ms, periodo.hasta_ms, idcondado)

    def rechazo_timeout_por_unidad(self, periodo: Periodo) -> list[dict]:
        return self.repository.rechazo_timeout_por_unidad(periodo.desde_ms, periodo.hasta_ms)

    def carga_por_unidad(self, periodo: Periodo) -> list[dict]:
        return self.repository.carga_por_unidad(periodo.desde_ms, periodo.hasta_ms)

    def ratio_demanda_capacidad(self, periodo: Periodo) -> list[dict]:
        return self.repository.ratio_demanda_capacidad(periodo.desde_ms, periodo.hasta_ms)
