"""Expediente completo — operador y cliente (RF-SEG-006 / CU-O29)."""

from __future__ import annotations

from typing import Any

from apps.accidentes.domain_constants import ESTADO_CERRADO
from apps.accidentes.services.consulta_enriquecimiento_service import (
    ConsultaEnriquecimientoService,
)
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
        enriquecimiento_svc: ConsultaEnriquecimientoService | None = None,
    ):
        self.accidentes = accidente_repo or AccidenteRepository()
        self.estado = estado_repo or EstadoAccidenteRepository()
        self.despachos = despacho_repo or DespachoRepository()
        self.historial_despacho = historial_despacho or HistorialDespachoRepository()
        self.geografia = geografia or GeografiaRepository()
        self.historial = historial_svc or HistorialEmergenciasService()
        self.pinot = pinot or PinotClient()
        self.enriquecimiento = enriquecimiento_svc or ConsultaEnriquecimientoService()

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

        idcondado = None
        idcalle = acc.get("idcalle")
        if idcalle is not None:
            idcondado = self.geografia.resolve_condado_from_idcalle(int(idcalle))

        if condados_permitidos is not None:
            if idcalle is None or idcondado not in condados_permitidos:
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
        notificaciones = self.pinot.query(
            "SELECT * FROM Fact_NotificacionDespacho WHERE idaccidente = %(idaccidente)s",
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

        try:
            enriquecimiento = self.enriquecimiento.obtener(idaccidente)
        except LookupError:
            enriquecimiento = {
                "idaccidente": idaccidente,
                "clima": None,
                "elementos_fisicos": [],
                "conductores": [],
                "implicados": [],
            }

        geo = None
        if idcalle is not None:
            geo = {
                "idcalle": int(idcalle),
                "idcondado": idcondado,
            }

        return {
            "accidente": acc,
            "estado_actual": est,
            "historial_estados_caso": self.estado.get_history(idaccidente),
            "despachos": despachos_detalle,
            "notificaciones_despacho": notificaciones,
            "notas": notas,
            "evidencias": evidencias,
            "enriquecimiento": enriquecimiento,
            "geografia": geo,
            "trayectoria_gps": gps_rows,
        }
