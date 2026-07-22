"""CU-O22 — asignación automática inteligente."""

from __future__ import annotations

from typing import Any

from apps.despacho.services.consulta_candidatas_service import ConsultaCandidatasService
from core.repositories.despacho.despacho_repository import DespachoRepository
from core.repositories.despacho.estado_accidente_despacho_repository import (
    EstadoAccidenteDespachoRepository,
)
from core.repositories.despacho.historial_despacho_repository import (
    ESTADO_PENDIENTE,
    HistorialDespachoRepository,
)
from core.repositories.despacho.notificacion_despacho_repository import (
    NotificacionDespachoRepository,
)

# Fact_Despacho.idorigendespacho es INT (FK a Dim_OrigenDespacho), no STRING.
# IDs deben coincidir con el seed en database/seed_catalogos.py.
ORIGEN_IDS: dict[str, int] = {
    "Automatico": 1,
    "Manual": 2,
    "Escalado_zona": 3,
}


class AsignacionInteligenteService:
    def __init__(
        self,
        candidatas_service: ConsultaCandidatasService | None = None,
        notificacion_service: object | None = None,
        despacho_repo: DespachoRepository | None = None,
        notificacion_repo: NotificacionDespachoRepository | None = None,
        historial_repo: HistorialDespachoRepository | None = None,
        estado_accidente_repo: EstadoAccidenteDespachoRepository | None = None,
    ):
        self.candidatas = candidatas_service or ConsultaCandidatasService()
        self._notificaciones_svc = notificacion_service
        self.despachos = despacho_repo or DespachoRepository()
        self.notificaciones = notificacion_repo or NotificacionDespachoRepository()
        self.historial = historial_repo or HistorialDespachoRepository()
        self.estado_accidente = estado_accidente_repo or EstadoAccidenteDespachoRepository()

    def ejecutar(
        self,
        *,
        idaccidente: str,
        idusuario: int = 0,
        idorigendespacho: str = "Automatico",
        incluir_vecinos: bool = False,
        idunidademergencia: int | None = None,
    ) -> dict[str, Any] | None:
        if idunidademergencia is not None:
            candidata = {"idunidademergencia": idunidademergencia}
        else:
            ranked = self.candidatas.listar_puntuadas(
                idaccidente, incluir_vecinos=incluir_vecinos
            )
            if not ranked:
                return None
            candidata = ranked[0]
        notif = self.notificaciones.publish_create(
            {
                "idaccidente": idaccidente,
                "idunidaddemergencia": candidata["idunidademergencia"],
                "numheridos": 0,
                "numvehiculos": 0,
            }
        )
        despacho = self.despachos.publish_create(
            {
                "idaccidente": idaccidente,
                "idunidademergencia": candidata["idunidademergencia"],
                "idnotificaciondespacho": notif["idnotificaciondespacho"],
                "idorigendespacho": ORIGEN_IDS[idorigendespacho],
                "activo": True,
            }
        )
        self.historial.publish(
            iddespacho=despacho["iddespacho"],
            estadonuevo=ESTADO_PENDIENTE,
        )
        self.estado_accidente.publish_buscando_unidad_if_first(
            idaccidente=idaccidente, idusuario=idusuario
        )
        entrega = self._get_notificacion_service().notificar(
            idnotificaciondespacho=notif["idnotificaciondespacho"],
            iddespacho=despacho["iddespacho"],
            idaccidente=idaccidente,
        )
        return {
            "idaccidente": idaccidente,
            "iddespacho": despacho["iddespacho"],
            "idnotificaciondespacho": notif["idnotificaciondespacho"],
            "idunidademergencia": candidata["idunidademergencia"],
            "origen": idorigendespacho,
            "entrega": entrega,
        }

    def _get_notificacion_service(self):
        if self._notificaciones_svc is None:
            from apps.despacho.services.notificacion_despacho_service import (
                NotificacionDespachoService,
            )

            self._notificaciones_svc = NotificacionDespachoService()
        return self._notificaciones_svc
