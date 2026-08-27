"""Resuelve el despacho activo en curso de la unidad autenticada (CU-O68/O70/O71).

Evita que el frontend dependa de recibir iddespacho/idaccidente por navegación:
la unidad puede entrar a "Mi seguimiento" desde el sidebar, refrescar la
página, o volver más tarde, y siempre debe ver su misión en curso si existe.
"""

from __future__ import annotations

from typing import Any

from core.repositories.accidentes.accidente_repository import AccidenteRepository
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
        accidente_repo: AccidenteRepository | None = None,
    ):
        self.despachos = despacho_repo or DespachoRepository()
        self.historial = historial_repo or HistorialDespachoRepository()
        self.accidentes = accidente_repo or AccidenteRepository()

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
                    # El panel de escalar severidad necesita los valores VIGENTES
                    # para precargarse. Sin ellos arrancaba en 0 heridos y el
                    # backend rechazaba el envío ("solo puede incrementarse") en
                    # cualquier caso que ya tuviera víctimas: eso era la "caída"
                    # del hallazgo #12.
                    **self._severidad_vigente(despacho["idaccidente"]),
                }
        return None

    def _severidad_vigente(self, idaccidente: str) -> dict[str, Any]:
        accidente = self.accidentes.find_by_id(idaccidente) or {}
        return {
            "idseveridad": accidente.get("idseveridad"),
            "numheridos": accidente.get("numheridos") or 0,
            "numfallecidos": accidente.get("numfallecidos") or 0,
        }
