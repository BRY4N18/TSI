"""Resuelve el despacho activo en curso de la unidad autenticada (CU-O25/O26/O39).

Evita que el frontend dependa de recibir iddespacho/idaccidente por navegación:
la unidad puede entrar a "Mi seguimiento" desde el sidebar, refrescar la
página, o volver más tarde, y siempre debe ver su misión en curso si existe.
"""

from __future__ import annotations

from typing import Any

from core.repositories.despacho.despacho_repository import DespachoRepository
from core.repositories.despacho.historial_despacho_repository import (
    ESTADO_CONFIRMADO,
    ESTADO_EN_SITIO,
    HistorialDespachoRepository,
)

ESTADOS_EN_CURSO = (ESTADO_CONFIRMADO, ESTADO_EN_SITIO)


class ObtenerMiSeguimientoActualService:
    def __init__(
        self,
        despacho_repo: DespachoRepository | None = None,
        historial_repo: HistorialDespachoRepository | None = None,
    ):
        self.despachos = despacho_repo or DespachoRepository()
        self.historial = historial_repo or HistorialDespachoRepository()

    def obtener(self, *, idunidademergencia: int) -> dict[str, Any] | None:
        activos = self.despachos.list_activos_by_unidad(idunidademergencia)
        for despacho in activos:
            estado, _ = self.historial.get_current_estado(despacho["iddespacho"])
            if estado in ESTADOS_EN_CURSO:
                return {
                    "iddespacho": despacho["iddespacho"],
                    "idaccidente": despacho["idaccidente"],
                    "idunidademergencia": idunidademergencia,
                    "estado_despacho": estado,
                }
        return None
