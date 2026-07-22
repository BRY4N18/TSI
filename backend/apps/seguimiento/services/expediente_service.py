"""Expediente completo — operador y cliente (RF-SEG-006)."""

from __future__ import annotations

from typing import Any

from apps.accidentes.domain_constants import ESTADO_CERRADO
from apps.seguimiento.services.historial_emergencias_service import (
    HistorialEmergenciasService,
)
from core.pinot.client import PinotClient
from core.repositories.accidentes.accidente_repository import AccidenteRepository
from core.repositories.accidentes.estado_accidente_repository import (
    EstadoAccidenteRepository,
)
from core.repositories.despacho.despacho_repository import DespachoRepository
from core.repositories.despacho.geografia_repository import GeografiaRepository
from core.repositories.despacho.historial_despacho_repository import (
    HistorialDespachoRepository,
)


class ExpedienteService:
    def __init__(
        self,
        accidente_repo: AccidenteRepository | None = None,
        estado_repo: EstadoAccidenteRepository | None = None,
        despacho_repo: DespachoRepository | None = None,
        historial_despacho: HistorialDespachoRepository | None = None,
        geografia: GeografiaRepository | None = None,
        historial_svc: HistorialEmergenciasService | None = None,
        pinot: PinotClient | None = None,
    ):
        self.accidentes = accidente_repo or AccidenteRepository()
        self.estado = estado_repo or EstadoAccidenteRepository()
        self.despachos = despacho_repo or DespachoRepository()
        self.historial_despacho = historial_despacho or HistorialDespachoRepository()
        self.geografia = geografia or GeografiaRepository()
        self.historial = historial_svc or HistorialEmergenciasService()
        self.pinot = pinot or PinotClient()

    def obtener(
        self,
        idaccidente: str,
        *,
        condados_permitidos: set[int] | None = None,
        requiere_cerrado: bool = False,
    ) -> dict[str, Any] | None:
        acc = self.accidentes.find_by_id(idaccidente)
        if not acc:
            return None
        est = self.estado.get_current_estado(idaccidente)
        if requiere_cerrado and est != ESTADO_CERRADO:
            return None
        if condados_permitidos is not None:
            idcalle = acc.get("idcalle")
            if idcalle is None:
                return None
            idcondado = self.geografia.resolve_condado_from_idcalle(int(idcalle))
            if idcondado not in condados_permitidos:
                return None

        despachos_detalle = []
        for d in self.despachos.list_by_accidente(idaccidente):
            historial = self.historial_despacho.list_by_despacho(int(d["iddespacho"]))
            despachos_detalle.append(
                {
                    "despacho": d,
                    "historial_estados": historial,
                }
            )

        notas = self.pinot.query(
            "SELECT * FROM Dim_NotaAccidente WHERE idaccidente = %(idaccidente)s",
            {"idaccidente": idaccidente},
        )
        evidencias = self.pinot.query(
            "SELECT * FROM Dim_EvidenciaFoto WHERE idaccidente = %(idaccidente)s",
            {"idaccidente": idaccidente},
        )
        gps_rows = []
        for d in self.despachos.list_by_accidente(idaccidente):
            uid = int(d["idunidademergencia"])
            puntos = self.pinot.query(
                """
                SELECT * FROM Dim_HistorialUbicacionUnidadEmergencia
                WHERE idunidademergencia = %(idunidademergencia)s
                """,
                {"idunidademergencia": uid},
            )
            gps_rows.extend(puntos)

        return {
            "accidente": acc,
            "estado_actual": est,
            "historial_estados_caso": self.estado.get_history(idaccidente),
            "despachos": despachos_detalle,
            "notas": notas,
            "evidencias": evidencias,
            "trayectoria_gps": gps_rows,
        }
