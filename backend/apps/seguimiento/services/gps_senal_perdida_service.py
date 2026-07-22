"""CU-O37 — detección señal GPS perdida."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from core.repositories.accidentes.nota_accidente_repository import (
    NotaAccidenteRepository,
)
from core.repositories.despacho.despacho_repository import DespachoRepository
from core.repositories.despacho.historial_despacho_repository import (
    ESTADO_CONFIRMADO,
    HistorialDespachoRepository,
)
from core.repositories.seguimiento.historial_ubicacion_repository import (
    HistorialUbicacionRepository,
)
from core.repositories.seguimiento.parametros_seguimiento_repository import (
    ParametrosSeguimientoRepository,
)


class GpsSenalPerdidaService:
    def __init__(
        self,
        despacho_repo: DespachoRepository | None = None,
        historial_despacho: HistorialDespachoRepository | None = None,
        historial_ubicacion: HistorialUbicacionRepository | None = None,
        parametros: ParametrosSeguimientoRepository | None = None,
        notas: NotaAccidenteRepository | None = None,
    ):
        self.despachos = despacho_repo or DespachoRepository()
        self.historial_despacho = historial_despacho or HistorialDespachoRepository()
        self.historial_ubicacion = historial_ubicacion or HistorialUbicacionRepository()
        self.parametros = parametros or ParametrosSeguimientoRepository()
        self.notas = notas or NotaAccidenteRepository()

    def evaluar_unidades_en_camino(self, *, idusuario_operador: int = 0) -> list[dict[str, Any]]:
        now = int(datetime.now(timezone.utc).timestamp() * 1000)
        umbral_seg = self.parametros.get()["gps_umbral_senal_perdida_seg"]
        alertas: list[dict[str, Any]] = []
        for d in self.despachos.pinot.query("SELECT * FROM Fact_Despacho WHERE activo = true", {}):
            idd = int(d["iddespacho"])
            estado, _ = self.historial_despacho.get_current_estado(idd)
            if estado != ESTADO_CONFIRMADO:
                continue
            uid = int(d["idunidademergencia"])
            last = self.historial_ubicacion.latest_fechahora(uid)
            if last is None or (now - last) / 1000.0 > umbral_seg:
                nota = self.notas.create_alerta(
                    idaccidente=d["idaccidente"],
                    idusuario=idusuario_operador,
                    nota=f"Señal GPS perdida unidad {uid} despacho {idd}",
                )
                alertas.append(
                    {
                        "iddespacho": idd,
                        "idunidademergencia": uid,
                        "idaccidente": d["idaccidente"],
                        "nota": nota,
                    }
                )
        return alertas
