"""La unidad da por terminada su parte de la atención (SRS §3.6.4).

Es la vía normal por la que un despacho llega a `Retirado`. Antes no existía:
la unidad solo podía registrar llegada o abortar, así que la única forma de
retirar a alguien era el retiro forzado desde central —que el SRS reserva para
"cuando un técnico olvida cerrar su parte"— o el cierre del caso, que retiraba
a todos en silencio. Sin esta acción, la regla "un caso solo pasa a cerrado
cuando todas las unidades se han retirado" no podía cumplirse por el camino
previsto.
"""

from __future__ import annotations

from typing import Any

from core.repositories.despacho.despacho_repository import DespachoRepository
from core.repositories.despacho.historial_despacho_repository import (
    ESTADO_CONFIRMADO,
    ESTADO_EN_SITIO,
    HistorialDespachoRepository,
)

from apps.seguimiento.services.retiro_despacho_service import RetiroDespachoService

RETIRABLES = (ESTADO_CONFIRMADO, ESTADO_EN_SITIO)


class FinalizarAtencionUnidadService:
    def __init__(
        self,
        despacho_repo: DespachoRepository | None = None,
        historial_repo: HistorialDespachoRepository | None = None,
        retiro: RetiroDespachoService | None = None,
    ):
        self.despachos = despacho_repo or DespachoRepository()
        self.historial = historial_repo or HistorialDespachoRepository()
        self.retiro = retiro or RetiroDespachoService()

    def finalizar(
        self, *, iddespacho: int, idunidademergencia: int, idusuario: int
    ) -> dict[str, Any]:
        despacho = self.despachos.find_by_id(iddespacho)
        if not despacho:
            raise LookupError("Despacho no encontrado")
        if int(despacho["idunidademergencia"]) != idunidademergencia:
            raise PermissionError("Despacho no pertenece a la unidad")

        estado, _ = self.historial.get_current_estado(iddespacho)
        if estado not in RETIRABLES:
            raise ValueError(
                f"No se puede finalizar la atención desde el estado '{estado}'"
            )

        resultado = self.retiro.retirar(
            iddespacho=iddespacho, idusuario=idusuario, forzado=False
        )
        # No cierra el caso: el cierre lo hace el Operador con su informe final,
        # y solo puede hacerlo cuando **todas** las unidades se han retirado.
        pendientes = self._despachos_sin_retirar(despacho["idaccidente"])
        return {
            "iddespacho": iddespacho,
            "idaccidente": despacho["idaccidente"],
            "fechahoraretiro": resultado["fechahoraretiro"],
            "unidades_sin_retirar": pendientes,
            "caso_listo_para_cierre": pendientes == 0,
        }

    def _despachos_sin_retirar(self, idaccidente: str) -> int:
        from core.repositories.despacho.historial_despacho_repository import (
            ESTADO_ABORTADO,
            ESTADO_RETIRADO,
        )

        pendientes = 0
        for d in self.despachos.list_by_accidente(idaccidente):
            estado, _ = self.historial.get_current_estado(int(d["iddespacho"]))
            if estado not in (ESTADO_RETIRADO, ESTADO_ABORTADO):
                pendientes += 1
        return pendientes
