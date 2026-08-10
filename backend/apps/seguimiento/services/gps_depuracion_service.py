"""Retención GPS — reporta puntos fuera del período de retención configurado.

Decisión 2026-08-08: las posiciones GPS **no se borran**. Se conservan
indefinidamente como muestra histórica para análisis futuro (siniestralidad,
auditoría de rutas). Este servicio nunca elimina filas de
`Dim_HistorialUbicacionUnidadEmergencia`; solo identifica y cuenta qué puntos
quedarían fuera de la ventana de retención configurada (`gps_retencion_dias`),
para reporte/monitoreo — no ejecuta ninguna purga.
"""

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
        # Recorrido por bloques: antes esto era un list_by_unidad() sin LIMIT, y
        # Pinot lo recortaba en silencio a 10 filas, asi que el job decidia que
        # conservar mirando solo los primeros 10 puntos de la traza.
        puntos = list(self.historial.iter_by_unidad(uid))
        if not puntos:
            return set()
        puntos.sort(key=lambda p: p.get("fechahora", 0))
        conservar: set[int] = {int(puntos[0]["idhistorialunidademergencia"])}

        llegada_ts = despacho.get("fechahorallegada")
        if llegada_ts:
            conservar.add(int(self._closest(puntos, int(llegada_ts))["idhistorialunidademergencia"]))

        retiro_ts = despacho.get("fechahoraretiro")
        if retiro_ts:
            conservar.add(int(self._closest(puntos, int(retiro_ts))["idhistorialunidademergencia"]))
        elif len(puntos) > 1:
            conservar.add(int(puntos[-1]["idhistorialunidademergencia"]))
        return conservar

    def depurar(self) -> dict[str, Any]:
        """Reporta cuántos puntos GPS quedan fuera de la ventana de retención.

        No borra nada (decisión 2026-08-08): todas las posiciones se conservan
        como muestra histórica. `elegibles_para_muestreo` cuenta los puntos que,
        de existir un proceso de análisis/archivado futuro, serían candidatos a
        revisar primero por antigüedad — informativo únicamente.
        """
        now = int(datetime.now(timezone.utc).timestamp() * 1000)
        retencion_dias = self.parametros.get()["gps_retencion_dias"]
        cutoff = now - retencion_dias * 86_400_000
        total_elegibles = 0
        for d in self.despachos.pinot.query("SELECT * FROM Fact_Despacho", {}):
            idd = int(d["iddespacho"])
            conservar = self.puntos_a_conservar(idd)
            uid = int(d["idunidademergencia"])
            for p in self.historial.iter_by_unidad(uid):
                pid = int(p["idhistorialunidademergencia"])
                if pid in conservar:
                    continue
                if int(p.get("fechahora", 0)) < cutoff:
                    total_elegibles += 1
        return {"elegibles_para_muestreo": total_elegibles, "retencion_dias": retencion_dias}

    @staticmethod
    def _closest(puntos: list[dict[str, Any]], ts: int) -> dict[str, Any]:
        return min(puntos, key=lambda p: abs(int(p.get("fechahora", 0)) - ts))
