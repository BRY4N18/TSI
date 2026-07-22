"""CU-O59 — el Operador declara disponibilidad de una unidad externa sin login propio."""

from __future__ import annotations

from typing import Any

from core.repositories.despacho.historial_estado_unidad_repository import (
    ESTADO_ACTIVA,
    ESTADO_EN_MISION,
    HistorialEstadoUnidadRepository,
)
from core.repositories.red_operativa.despacho_activo_read_repository import (
    DespachoActivoReadRepository,
)


class DisponibilidadExternaService:
    def __init__(
        self,
        historial_repo: HistorialEstadoUnidadRepository | None = None,
        despacho_repo: DespachoActivoReadRepository | None = None,
    ):
        self.historial_repo = historial_repo or HistorialEstadoUnidadRepository()
        self.despacho_repo = despacho_repo or DespachoActivoReadRepository()

    def declarar(
        self,
        *,
        idunidademergencia: int,
        estadonuevo: str,
        idusuario_operador: int,
    ) -> dict[str, Any]:
        if estadonuevo == ESTADO_EN_MISION:
            raise PermissionError('"En Misión" es de asignación exclusiva del sistema')

        if estadonuevo == ESTADO_ACTIVA and self.despacho_repo.has_despacho_activo(
            idunidademergencia
        ):
            raise ValueError(
                "Inconsistencia: la unidad tiene un despacho activo sin retirar"
            )

        return self.historial_repo.append_estado(
            idunidademergencia=idunidademergencia,
            estadonuevo=estadonuevo,
            idusuario=idusuario_operador,
        )
