"""RF-TIC-003 (CU-O95) — configuración de SLA con vigencia temporal."""

from __future__ import annotations

from core.repositories.soporte.sla_config_repository import SLAConfigRepository

_RANGO_TIEMPO_MIN_SEG = 1


class ConfigurarSLAService:
    def __init__(self, sla_config_repo: SLAConfigRepository | None = None):
        self.sla_config_repo = sla_config_repo or SLAConfigRepository()

    def listar(self) -> list[dict]:
        return self.sla_config_repo.list()

    def _validar_tiempos(self, tiemporespuestamax: int, tiemporesolucionmax: int) -> None:
        if tiemporespuestamax < _RANGO_TIEMPO_MIN_SEG or tiemporesolucionmax < _RANGO_TIEMPO_MIN_SEG:
            raise ValueError("Los tiempos de SLA deben ser mayores a 0 segundos")
        if tiemporespuestamax > tiemporesolucionmax:
            raise ValueError("tiemporespuestamax no puede ser mayor que tiemporesolucionmax")

    def crear(
        self,
        *,
        idplan: int,
        tipoincidencia: str,
        prioridad: str,
        tiemporespuestamax: int,
        tiemporesolucionmax: int,
    ) -> dict:
        self._validar_tiempos(tiemporespuestamax, tiemporesolucionmax)
        return self.sla_config_repo.crear_regla(
            idplan=idplan,
            tipoincidencia=tipoincidencia,
            prioridad=prioridad,
            tiemporespuestamax=tiemporespuestamax,
            tiemporesolucionmax=tiemporesolucionmax,
        )

    def modificar(
        self, idslaconfig: int, *, tiemporespuestamax: int, tiemporesolucionmax: int
    ) -> dict:
        self._validar_tiempos(tiemporespuestamax, tiemporesolucionmax)
        return self.sla_config_repo.modificar_regla(
            idslaconfig,
            tiemporespuestamax=tiemporespuestamax,
            tiemporesolucionmax=tiemporesolucionmax,
        )
