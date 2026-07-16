"""Retiro unitario de despacho — compartido O28/O42/O44."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from core.repositories.despacho.despacho_repository import DespachoRepository
from core.repositories.despacho.historial_despacho_repository import (
    ESTADO_ABORTADO,
    ESTADO_RETIRADO,
    HistorialDespachoRepository,
)
from core.repositories.despacho.historial_estado_unidad_repository import (
    ESTADO_ACTIVA,
    ESTADO_FUERA_SERVICIO,
    HistorialEstadoUnidadRepository,
)


class RetiroDespachoService:
    def __init__(
        self,
        despacho_repo: DespachoRepository | None = None,
        historial_repo: HistorialDespachoRepository | None = None,
        historial_unidad: HistorialEstadoUnidadRepository | None = None,
    ):
        self.despachos = despacho_repo or DespachoRepository()
        self.historial = historial_repo or HistorialDespachoRepository()
        self.historial_unidad = historial_unidad or HistorialEstadoUnidadRepository()

    def retirar(self, *, iddespacho: int, idusuario: int) -> dict[str, Any]:
        despacho = self.despachos.find_by_id(iddespacho)
        if not despacho:
            raise LookupError("Despacho no encontrado")
        estado, _ = self.historial.get_current_estado(iddespacho)
        if estado == ESTADO_RETIRADO:
            raise ValueError("Despacho ya retirado")
        if estado == ESTADO_ABORTADO:
            raise ValueError("Despacho abortado no retirable")

        now = int(datetime.now(timezone.utc).timestamp() * 1000)
        self.historial.publish(
            iddespacho=iddespacho,
            estadonuevo=ESTADO_RETIRADO,
            idusuario=idusuario,
        )
        self.despachos.publish_update(
            iddespacho,
            {"fechahoraretiro": now, "activo": False},
        )
        idunidad = int(despacho["idunidademergencia"])
        estado_unidad_actual, _ = self.historial_unidad.get_current_estado(idunidad)
        estado_unidad_destino = (
            ESTADO_FUERA_SERVICIO
            if estado_unidad_actual == ESTADO_FUERA_SERVICIO
            else ESTADO_ACTIVA
        )
        self.historial_unidad.append_estado(
            idunidademergencia=idunidad,
            estadonuevo=estado_unidad_destino,
            idusuario=idusuario,
        )
        return {"iddespacho": iddespacho, "fechahoraretiro": now}

    def todos_retirados_o_abortados(self, idaccidente: str) -> bool:
        despachos = self.despachos.list_by_accidente(idaccidente)
        if not despachos:
            return False
        for d in despachos:
            estado, _ = self.historial.get_current_estado(int(d["iddespacho"]))
            if estado not in (ESTADO_RETIRADO, ESTADO_ABORTADO):
                return False
        return True
