"""CU-O45 — rechazar despacho."""

from __future__ import annotations

from typing import Any

from apps.despacho.services.reasignacion_despacho_service import (
    ReasignacionDespachoService,
)
from core.repositories.despacho.despacho_repository import DespachoRepository
from core.repositories.despacho.historial_despacho_repository import (
    ESTADO_PENDIENTE,
    ESTADO_RECHAZADO,
    HistorialDespachoRepository,
)
from core.repositories.despacho.notificacion_despacho_repository import (
    ESTADO_CONFIRMADA,
    ESTADO_RECHAZADA,
    NotificacionDespachoRepository,
)


class RechazarDespachoService:
    def __init__(
        self,
        notificacion_repo: NotificacionDespachoRepository | None = None,
        despacho_repo: DespachoRepository | None = None,
        historial_repo: HistorialDespachoRepository | None = None,
        reasignacion: ReasignacionDespachoService | None = None,
    ):
        self.notificaciones = notificacion_repo or NotificacionDespachoRepository()
        self.despachos = despacho_repo or DespachoRepository()
        self.historial = historial_repo or HistorialDespachoRepository()
        self.reasignacion = reasignacion or ReasignacionDespachoService()

    def rechazar(
        self,
        *,
        idnotificaciondespacho: int,
        idunidademergencia: int,
        motivo: str,
        idusuario: int = 0,
    ) -> dict[str, Any]:
        notif = self.notificaciones.find_by_id(idnotificaciondespacho)
        if not notif:
            raise LookupError("Notificación no encontrada")
        if int(notif["idunidaddemergencia"]) != idunidademergencia:
            raise PermissionError("Notificación no pertenece a la unidad")
        if notif.get("estadonotificaciondespacho") in (ESTADO_CONFIRMADA, ESTADO_RECHAZADA):
            raise ValueError("Notificación ya respondida")
        despachos = [
            d
            for d in self.despachos.list_by_accidente(notif["idaccidente"], activo=True)
            if d.get("idnotificaciondespacho") == idnotificaciondespacho
        ]
        if not despachos:
            raise LookupError("Despacho no encontrado")
        despacho = despachos[0]
        self.notificaciones.publish_update(
            idnotificaciondespacho,
            {"estadonotificaciondespacho": ESTADO_RECHAZADA, "motivo": motivo},
        )
        self.despachos.publish_update(despacho["iddespacho"], {"activo": False})
        self.historial.publish(
            iddespacho=despacho["iddespacho"],
            estadonuevo=ESTADO_RECHAZADO,
            estadoanterior=ESTADO_PENDIENTE,
        )
        result = self.reasignacion.ejecutar(
            idaccidente=notif["idaccidente"], idusuario=idusuario
        )
        return {
            "message": "Despacho rechazado",
            "idaccidente": notif["idaccidente"],
            "iddespacho": despacho["iddespacho"],
            "reasignacion_iniciada": result.get("reasignacion_iniciada", False),
        }
