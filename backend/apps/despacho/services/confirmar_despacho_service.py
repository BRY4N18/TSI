"""CU-O24 — confirmar despacho."""

from __future__ import annotations

from typing import Any

from core.repositories.despacho.despacho_repository import DespachoRepository
from core.repositories.despacho.estado_accidente_despacho_repository import (
    EstadoAccidenteDespachoRepository,
)
from core.repositories.despacho.historial_despacho_repository import (
    ESTADO_CONFIRMADO,
    ESTADO_PENDIENTE,
    HistorialDespachoRepository,
)
from core.repositories.despacho.historial_estado_unidad_repository import (
    ESTADO_EN_MISION,
    HistorialEstadoUnidadRepository,
)
from core.repositories.despacho.notificacion_despacho_repository import (
    ESTADO_CONFIRMADA,
    ESTADO_NOTIFICADA,
    NotificacionDespachoRepository,
)
from core.repositories.despacho.notificacion_despacho_repository import (
    ESTADO_PENDIENTE as NOTIF_PENDIENTE,
)


class ConfirmarDespachoService:
    def __init__(
        self,
        notificacion_repo: NotificacionDespachoRepository | None = None,
        despacho_repo: DespachoRepository | None = None,
        historial_repo: HistorialDespachoRepository | None = None,
        historial_unidad_repo: HistorialEstadoUnidadRepository | None = None,
        estado_accidente_repo: EstadoAccidenteDespachoRepository | None = None,
    ):
        self.notificaciones = notificacion_repo or NotificacionDespachoRepository()
        self.despachos = despacho_repo or DespachoRepository()
        self.historial = historial_repo or HistorialDespachoRepository()
        self.historial_unidad = historial_unidad_repo or HistorialEstadoUnidadRepository()
        self.estado_accidente = estado_accidente_repo or EstadoAccidenteDespachoRepository()

    def confirmar(
        self,
        *,
        idnotificaciondespacho: int,
        idunidademergencia: int,
        idusuario: int,
    ) -> dict[str, Any]:
        notif = self.notificaciones.find_by_id(idnotificaciondespacho)
        if not notif:
            raise LookupError("Notificación no encontrada")
        if int(notif["idunidaddemergencia"]) != idunidademergencia:
            raise PermissionError("Notificación no pertenece a la unidad")
        estado_notif = notif.get("estadonotificaciondespacho")
        if estado_notif in (ESTADO_CONFIRMADA, "Rechazada", "No_entregada"):
            raise ValueError("Notificación ya respondida")
        if estado_notif not in (NOTIF_PENDIENTE, ESTADO_NOTIFICADA):
            raise ValueError("Notificación no confirmable")
        despachos = [
            d
            for d in self.despachos.list_by_accidente(notif["idaccidente"], activo=True)
            if d.get("idnotificaciondespacho") == idnotificaciondespacho
        ]
        if not despachos:
            raise LookupError("Despacho no encontrado")
        despacho = despachos[0]
        self.notificaciones.publish_update(
            idnotificaciondespacho, {"estadonotificaciondespacho": ESTADO_CONFIRMADA}
        )
        self.historial.publish(
            iddespacho=despacho["iddespacho"],
            estadonuevo=ESTADO_CONFIRMADO,
            estadoanterior=ESTADO_PENDIENTE,
        )
        self.historial_unidad.append_estado(
            idunidademergencia=idunidademergencia,
            estadonuevo=ESTADO_EN_MISION,
            idusuario=idusuario,
        )
        estado_caso = self.estado_accidente.publish_asignado_if_first_confirmed(
            idaccidente=notif["idaccidente"], idusuario=idusuario
        )
        return {
            "message": "Despacho confirmado",
            "idaccidente": notif["idaccidente"],
            "iddespacho": despacho["iddespacho"],
            "idunidademergencia": idunidademergencia,
            "estado_caso": "ASIGNADO" if estado_caso else "BUSCANDO_UNIDAD",
            "estado_unidad": ESTADO_EN_MISION,
        }
