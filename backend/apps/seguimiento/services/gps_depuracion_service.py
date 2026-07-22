"""Depuración GPS — conserva 3 puntos por despacho (origen, llegada, cierre)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from core.repositories.despacho.despacho_repository import DespachoRepository
from core.repositories.seguimiento.historial_ubicacion_repository import (
    HistorialUbicacionRepository,
)
from core.repositories.seguimiento.parametros_seguimiento_repository import (
    ParametrosSeguimientoRepository,
)


class GpsDepuracionService:
    def __init__(
        self,
        despacho_repo: DespachoRepository | None = None,
        historial_ubicacion: HistorialUbicacionRepository | None = None,
        parametros: ParametrosSeguimientoRepository | None = None,
    ):
        self.despachos = despacho_repo or DespachoRepository()
        self.historial = historial_ubicacion or HistorialUbicacionRepository()
        self.parametros = parametros or ParametrosSeguimientoRepository()

    def puntos_a_conservar(self, iddespacho: int) -> set[int]:
        despacho = self.despachos.find_by_id(iddespacho)
        if not despacho:
            return set()
        uid = int(despacho["idunidademergencia"])
        puntos = self.historial.list_by_unidad(uid)
        if not puntos:
            return set()
        puntos.sort(key=lambda p: p.get("fechahora", 0))
        conservar: set[int] = {int(puntos[0]["idhistorialubicacion"])}

        llegada_ts = despacho.get("fechahorallegada")
        if llegada_ts:
            conservar.add(int(self._closest(puntos, int(llegada_ts))["idhistorialubicacion"]))

        retiro_ts = despacho.get("fechahoraretiro")
        if retiro_ts:
            conservar.add(int(self._closest(puntos, int(retiro_ts))["idhistorialubicacion"]))
        elif len(puntos) > 1:
            conservar.add(int(puntos[-1]["idhistorialubicacion"]))
        return conservar

    def depurar(self) -> dict[str, Any]:
        now = int(datetime.now(timezone.utc).timestamp() * 1000)
        retencion_dias = self.parametros.get()["gps_retencion_dias"]
        cutoff = now - retencion_dias * 86_400_000
        total_depurados = 0
        for d in self.despachos.pinot.query("SELECT * FROM Fact_Despacho", {}):
            idd = int(d["iddespacho"])
            conservar = self.puntos_a_conservar(idd)
            uid = int(d["idunidademergencia"])
            for p in self.historial.list_by_unidad(uid):
                pid = int(p["idhistorialubicacion"])
                if pid in conservar:
                    continue
                if int(p.get("fechahora", 0)) < cutoff:
                    total_depurados += 1
        return {"depurados": total_depurados, "retencion_dias": retencion_dias}

    @staticmethod
    def _closest(puntos: list[dict[str, Any]], ts: int) -> dict[str, Any]:
        return min(puntos, key=lambda p: abs(int(p.get("fechahora", 0)) - ts))
