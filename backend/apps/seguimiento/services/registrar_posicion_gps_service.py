"""CU-O25 — ingestión GPS + geofencing O26."""

from __future__ import annotations

from typing import Any

from core.repositories.despacho.despacho_repository import DespachoRepository
from core.repositories.despacho.historial_despacho_repository import (
    ESTADO_CONFIRMADO,
    HistorialDespachoRepository,
)
from core.repositories.seguimiento.expediente_repository import ExpedienteRepository
from core.repositories.seguimiento.historial_ubicacion_repository import HistorialUbicacionRepository
from core.repositories.seguimiento.parametros_seguimiento_repository import (
    ParametrosSeguimientoRepository,
)
from core.repositories.seguimiento.unidad_snapshot_repository import UnidadSnapshotRepository

from apps.seguimiento.services.geofencing_evaluator import GeofencingEvaluator
from apps.seguimiento.services.registrar_llegada_service import RegistrarLlegadaService
from apps.seguimiento.services.seguimiento_sse_service import SeguimientoSseService
from apps.seguimiento.services.eta_calculo_service import EtaCalculoService


class RegistrarPosicionGpsService:
    def __init__(
        self,
        historial_ubicacion: HistorialUbicacionRepository | None = None,
        snapshot_repo: UnidadSnapshotRepository | None = None,
        despacho_repo: DespachoRepository | None = None,
        historial_despacho: HistorialDespachoRepository | None = None,
        accidente_repo: ExpedienteRepository | None = None,
        parametros_repo: ParametrosSeguimientoRepository | None = None,
        llegada_service: RegistrarLlegadaService | None = None,
        geofence: GeofencingEvaluator | None = None,
        sse: SeguimientoSseService | None = None,
        eta_svc: EtaCalculoService | None = None,
    ):
        self.historial_ubicacion = historial_ubicacion or HistorialUbicacionRepository()
        self.snapshot = snapshot_repo or UnidadSnapshotRepository()
        self.despacho = despacho_repo or DespachoRepository()
        self.historial_despacho = historial_despacho or HistorialDespachoRepository()
        self.accidente = accidente_repo or ExpedienteRepository()
        self.parametros = parametros_repo or ParametrosSeguimientoRepository()
        self.llegada = llegada_service or RegistrarLlegadaService()
        self._geofence = geofence or GeofencingEvaluator()
        self._sse = sse or SeguimientoSseService()
        self._eta = eta_svc or EtaCalculoService()

    def registrar(
        self,
        *,
        idunidademergencia: int,
        idaccidente: str,
        latitud: float,
        longitud: float,
        fechahora: int,
        idusuario: int,
    ) -> dict[str, Any]:
        despachos = self.despacho.list_by_accidente(idaccidente, activo=True)
        despacho_unidad = next(
            (
                d for d in despachos
                if int(d["idunidademergencia"]) == idunidademergencia
            ),
            None,
        )
        if not despacho_unidad:
            raise ValueError("Unidad sin despacho activo para el caso")
        iddespacho = int(despacho_unidad["iddespacho"])
        estado, _ = self.historial_despacho.get_current_estado(iddespacho)
        if estado != ESTADO_CONFIRMADO:
            raise ValueError("Despacho no está en camino (Confirmado)")

        self.historial_ubicacion.publish(
            idunidademergencia=idunidademergencia,
            idaccidente=idaccidente,
            latitud=latitud,
            longitud=longitud,
            fechahora=fechahora,
        )
        self.snapshot.publish_snapshot(
            idunidademergencia=idunidademergencia,
            latitud=latitud,
            longitud=longitud,
            fechahora=fechahora,
        )
        self._sse.publish(
            "seguimiento.posicion",
            {
                "idunidademergencia": idunidademergencia,
                "latitud": latitud,
                "longitud": longitud,
                "idaccidente": idaccidente,
                "fechahora": fechahora,
            },
        )

        llegada_automatica = False
        accidente = self.accidente.find_accidente(idaccidente)
        if accidente:
            dest_lat = float(accidente.get("latitudinicio", 0))
            dest_lon = float(accidente.get("longitudinicio", 0))
            eta_min = self._eta.eta_minutos(latitud, longitud, dest_lat, dest_lon)
            self._sse.publish(
                "seguimiento.eta",
                {
                    "idunidademergencia": idunidademergencia,
                    "idaccidente": idaccidente,
                    "eta_minutos": eta_min,
                },
            )
            params = self.parametros.get()
            puntos = [
                (float(r["latitud"]), float(r["longitud"]), int(r["fechahora"]))
                for r in self.historial_ubicacion.list_by_unidad(idunidademergencia)
            ]
            if self._geofence.evaluar_llegada_desde_puntos(
                puntos=puntos,
                dest_lat=dest_lat,
                dest_lon=dest_lon,
                fechahora_ms=fechahora,
                radio_metros=float(params["geofence_radio_metros"]),
                histéresis_seg=int(params["geofence_histéresis_seg"]),
            ):
                self.llegada.registrar(
                    iddespacho=iddespacho,
                    idunidademergencia=idunidademergencia,
                    idusuario=idusuario,
                )
                llegada_automatica = True

        return {"aceptado": True, "llegada_automatica": llegada_automatica}
