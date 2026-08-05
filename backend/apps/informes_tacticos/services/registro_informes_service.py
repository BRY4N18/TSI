from __future__ import annotations

from apps.informes_tacticos.periodo import Periodo
from core.repositories.informes_tacticos.registro_repository import RegistroRepository

DEFAULT_TOP = 10


class RegistroInformesService:
    def __init__(self, repository: RegistroRepository | None = None):
        self.repository = repository or RegistroRepository()

    def volumen_casos(self, periodo: Periodo) -> list[dict]:
        return self.repository.volumen_casos(periodo.desde_ms, periodo.hasta_ms, periodo.datetrunc_unit)

    def distribucion_severidad(self, periodo: Periodo) -> list[dict]:
        return self.repository.distribucion_severidad(periodo.desde_ms, periodo.hasta_ms)

    def distribucion_zona(self, periodo: Periodo) -> list[dict]:
        return self.repository.distribucion_zona(periodo.desde_ms, periodo.hasta_ms)

    def completitud_campos_criticos(self, periodo: Periodo) -> list[dict]:
        return self.repository.completitud_campos_criticos(
            periodo.desde_ms, periodo.hasta_ms, periodo.datetrunc_unit
        )

    def descarte_fusion(self, periodo: Periodo) -> list[dict]:
        return self.repository.descarte_fusion(periodo.desde_ms, periodo.hasta_ms, periodo.datetrunc_unit)

    def ranking_ubicaciones(self, periodo: Periodo, top: int = DEFAULT_TOP) -> list[dict]:
        return self.repository.ranking_ubicaciones(periodo.desde_ms, periodo.hasta_ms, top)

    def impacto_humano(self, periodo: Periodo) -> list[dict]:
        return self.repository.impacto_humano(periodo.desde_ms, periodo.hasta_ms)
