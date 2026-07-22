"""CU-O26 — registro manual/automático de llegada al sitio."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from apps.accidentes.domain_constants import ESTADO_EN_ATENCION
from core.repositories.accidentes.estado_accidente_repository import (
    EstadoAccidenteRepository,
)
from core.repositories.despacho.despacho_repository import DespachoRepository
from core.repositories.despacho.historial_despacho_repository import (
    ESTADO_CONFIRMADO,
    ESTADO_EN_SITIO,
    HistorialDespachoRepository,
)


class RegistrarLlegadaService:
    def __init__(
        self,
        despacho_repo: DespachoRepository | None = None,
        historial_repo: HistorialDespachoRepository | None = None,
        estado_repo: EstadoAccidenteRepository | None = None,
    ):
        self.despacho = despacho_repo or DespachoRepository()
        self.historial = historial_repo or HistorialDespachoRepository()
        self.estado = estado_repo or EstadoAccidenteRepository()

    def registrar(
        self,
        *,
        iddespacho: int,
        idunidademergencia: int,
        idusuario: int,
    ) -> dict[str, Any]:
        despacho = self.despacho.find_by_id(iddespacho)
        if not despacho:
            raise LookupError("Despacho no encontrado")
        if int(despacho["idunidademergencia"]) != idunidademergencia:
            raise PermissionError("Despacho no pertenece a la unidad")
        estado_actual, _ = self.historial.get_current_estado(iddespacho)
        if estado_actual == ESTADO_EN_SITIO:
            raise ValueError("Llegada ya registrada")
        if estado_actual != ESTADO_CONFIRMADO:
            raise ValueError(f"Estado inválido para llegada: {estado_actual}")

        now = int(datetime.now(timezone.utc).timestamp() * 1000)
        self.historial.publish(
            iddespacho=iddespacho,
            estadonuevo=ESTADO_EN_SITIO,
            idusuario=idusuario,
        )
        self.despacho.publish_update(
            iddespacho,
            {"fechahorallegada": now},
        )

        idaccidente = despacho["idaccidente"]
        current_caso = self.estado.get_current_estado(idaccidente)
        if current_caso != ESTADO_EN_ATENCION:
            self.estado.append_estado(
                idaccidente=idaccidente,
                estado=ESTADO_EN_ATENCION,
                idusuario=idusuario,
            )

        return {
            "iddespacho": iddespacho,
            "fechahorallegada": now,
            "estado_caso": ESTADO_EN_ATENCION,
        }
