"""Mapa operador — accidentes activos y unidades (RF-SEG-007)."""

from __future__ import annotations

from typing import Any

from apps.accidentes.domain_constants import (
    ESTADO_ASIGNADO,
    ESTADO_BUSCANDO_UNIDAD,
    ESTADO_CERRADO,
    ESTADO_DESCARTADO,
    ESTADO_EN_ATENCION,
    ESTADO_FUSIONADO,
)
from apps.seguimiento.services.eta_calculo_service import EtaCalculoService
from core.pinot.client import PinotClient
from core.repositories.accidentes.accidente_repository import AccidenteRepository
from core.repositories.accidentes.estado_accidente_repository import (
    EstadoAccidenteRepository,
)
from core.repositories.despacho.despacho_repository import DespachoRepository
from core.repositories.despacho.historial_despacho_repository import (
    ESTADO_CONFIRMADO,
    HistorialDespachoRepository,
)
from core.repositories.despacho.historial_estado_unidad_repository import (
    HistorialEstadoUnidadRepository,
)
from core.repositories.despacho.unidad_emergencia_repository import (
    UnidadEmergenciaRepository,
)

ESTADOS_ACTIVOS = {
    ESTADO_ASIGNADO,
    ESTADO_BUSCANDO_UNIDAD,
    ESTADO_EN_ATENCION,
}


class MapaSeguimientoService:
    def __init__(
        self,
        accidente_repo: AccidenteRepository | None = None,
        estado_repo: EstadoAccidenteRepository | None = None,
        despacho_repo: DespachoRepository | None = None,
        historial_despacho: HistorialDespachoRepository | None = None,
        unidad_repo: UnidadEmergenciaRepository | None = None,
        historial_unidad: HistorialEstadoUnidadRepository | None = None,
        eta: EtaCalculoService | None = None,
        pinot: PinotClient | None = None,
    ):
        self.accidentes = accidente_repo or AccidenteRepository()
        self.estado = estado_repo or EstadoAccidenteRepository()
        self.despachos = despacho_repo or DespachoRepository()
        self.historial_despacho = historial_despacho or HistorialDespachoRepository()
        self.unidades = unidad_repo or UnidadEmergenciaRepository()
        self.historial_unidad = historial_unidad or HistorialEstadoUnidadRepository()
        self.eta = eta or EtaCalculoService()
        self.pinot = pinot or PinotClient()

    def obtener_mapa(self) -> dict[str, Any]:
        accidentes_activos: list[dict[str, Any]] = []
        for acc in self.accidentes.list_activos(limit=100):
            est = self.estado.get_current_estado(acc["idaccidente"])
            if est in (ESTADO_CERRADO, ESTADO_DESCARTADO, ESTADO_FUSIONADO, None):
                continue
            if est not in ESTADOS_ACTIVOS and est != ESTADO_EN_ATENCION:
                continue
            accidentes_activos.append(
                {
                    "idaccidente": acc["idaccidente"],
                    "idseveridad": acc.get("idseveridad", 1),
                    "coordenadas": {
                        "latitud": float(acc.get("latitudinicio", 0)),
                        "longitud": float(acc.get("longitudinicio", 0)),
                    },
                    "estado": est,
                }
            )

        unidades_mapa: list[dict[str, Any]] = []
        for u in self.unidades.list_active():
            estado_u, _ = self.historial_unidad.get_current_estado(int(u["idunidademergencia"]))
            estado_fmt = estado_u.replace(" ", "_") if estado_u else "Fuera_de_servicio"
            idaccidente = None
            eta_min = None
            dist_km = None
            activos = self.despachos.list_activos_by_unidad(int(u["idunidademergencia"]))
            if activos:
                d = activos[0]
                idaccidente = d["idaccidente"]
                est_d, _ = self.historial_despacho.get_current_estado(int(d["iddespacho"]))
                if est_d == ESTADO_CONFIRMADO and idaccidente:
                    acc = self.accidentes.find_by_id(idaccidente)
                    if acc:
                        dist_km = self.eta.distancia_restante_km(
                            float(u.get("latitud", 0)),
                            float(u.get("longitud", 0)),
                            float(acc.get("latitudinicio", 0)),
                            float(acc.get("longitudinicio", 0)),
                        )
                        eta_min = self.eta.eta_minutos(
                            float(u.get("latitud", 0)),
                            float(u.get("longitud", 0)),
                            float(acc.get("latitudinicio", 0)),
                            float(acc.get("longitudinicio", 0)),
                        )
            unidades_mapa.append(
                {
                    "idunidademergencia": int(u["idunidademergencia"]),
                    "unidademergencia": u.get("unidademergencia", ""),
                    "estado_unidad": estado_fmt,
                    "coordenadas": {
                        "latitud": float(u.get("latitud", 0)),
                        "longitud": float(u.get("longitud", 0)),
                    },
                    "idaccidente": idaccidente,
                    "eta_minutos": eta_min,
                    "distancia_restante_km": dist_km,
                }
            )
        return {"accidentes_activos": accidentes_activos, "unidades": unidades_mapa}

    def obtener_seguimiento_accidente(self, idaccidente: str) -> dict[str, Any] | None:
        acc = self.accidentes.find_by_id(idaccidente)
        if not acc:
            return None
        estado_caso = self.estado.get_current_estado(idaccidente) or "REPORTADO"
        despachos_out: list[dict[str, Any]] = []
        for d in self.despachos.list_by_accidente(idaccidente):
            est, _ = self.historial_despacho.get_current_estado(int(d["iddespacho"]))
            uid = int(d["idunidademergencia"])
            unidad = self.unidades.find_by_id(uid)
            ruta = self.pinot.query(
                """
                SELECT latitud, longitud, fechahora
                FROM Dim_HistorialUbicacionUnidadEmergencia
                WHERE idunidademergencia = %(idunidademergencia)s
                """,
                {"idunidademergencia": uid},
            )
            ruta.sort(key=lambda r: r.get("fechahora", 0))
            despachos_out.append(
                {
                    "iddespacho": int(d["iddespacho"]),
                    "idunidademergencia": uid,
                    "unidademergencia": unidad.get("unidademergencia", "") if unidad else "",
                    "estado": est,
                    "fechahoradespacho": int(d.get("fechahoradespacho", 0)),
                    "fechahorallegada": d.get("fechahorallegada"),
                    "fechahoraretiro": d.get("fechahoraretiro"),
                    "eta_minutos": None,
                    "ruta_recorrida": [
                        {
                            "latitud": float(p["latitud"]),
                            "longitud": float(p["longitud"]),
                            "fechahora": int(p["fechahora"]),
                        }
                        for p in ruta
                    ],
                }
            )
        return {
            "idaccidente": idaccidente,
            "estado_caso": estado_caso,
            "coordenadas_accidente": {
                "latitud": float(acc.get("latitudinicio", 0)),
                "longitud": float(acc.get("longitudinicio", 0)),
            },
            "despachos": despachos_out,
        }
