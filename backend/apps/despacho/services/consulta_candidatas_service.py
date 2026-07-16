"""Filtrado y puntuación de unidades candidatas."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

DISPONIBILIDAD_MAX_MINUTOS = 30

from apps.despacho.services.concordancia_tipo_service import ConcordanciaTipoService
from apps.despacho.services.despacho_math import haversine_km
from core.repositories.accidentes.accidente_repository import AccidenteRepository
from core.repositories.despacho.despacho_repository import DespachoRepository
from core.repositories.despacho.geografia_repository import GeografiaRepository
from core.repositories.despacho.historial_estado_unidad_repository import (
    ESTADO_ACTIVA,
    HistorialEstadoUnidadRepository,
)
from core.repositories.despacho.notificacion_despacho_repository import (
    ESTADO_RECHAZADA,
    NotificacionDespachoRepository,
)
from core.repositories.despacho.parametros_despacho_repository import ParametrosDespachoRepository
from core.repositories.despacho.ubicacion_unidad_repository import UbicacionUnidadRepository
from core.repositories.despacho.unidad_emergencia_repository import UnidadEmergenciaRepository


class ConsultaCandidatasService:
    def __init__(
        self,
        accidente_repo: AccidenteRepository | None = None,
        unidad_repo: UnidadEmergenciaRepository | None = None,
        geografia_repo: GeografiaRepository | None = None,
        ubicacion_repo: UbicacionUnidadRepository | None = None,
        historial_unidad_repo: HistorialEstadoUnidadRepository | None = None,
        despacho_repo: DespachoRepository | None = None,
        notificacion_repo: NotificacionDespachoRepository | None = None,
        parametros_repo: ParametrosDespachoRepository | None = None,
        concordancia: ConcordanciaTipoService | None = None,
    ):
        self.accidentes = accidente_repo or AccidenteRepository()
        self.unidades = unidad_repo or UnidadEmergenciaRepository()
        self.geografia = geografia_repo or GeografiaRepository()
        self.ubicacion = ubicacion_repo or UbicacionUnidadRepository()
        self.historial_unidad = historial_unidad_repo or HistorialEstadoUnidadRepository()
        self.despachos = despacho_repo or DespachoRepository()
        self.notificaciones = notificacion_repo or NotificacionDespachoRepository()
        self.parametros = parametros_repo or ParametrosDespachoRepository()
        self.concordancia = concordancia or ConcordanciaTipoService(self.parametros)

    def listar_puntuadas(
        self,
        idaccidente: str,
        *,
        incluir_vecinos: bool = False,
        excluir_unidades: set[int] | None = None,
    ) -> list[dict[str, Any]]:
        accidente = self.accidentes.find_by_id(idaccidente)
        if not accidente:
            raise LookupError("Accidente no encontrado")
        idcalle = accidente.get("idcalle")
        if idcalle is None:
            return []
        idcondado = self.geografia.resolve_condado_from_idcalle(int(idcalle))
        if idcondado is None:
            return []
        vecinos = self.geografia.list_condados_vecinos(idcondado) if incluir_vecinos else []
        candidatas = self.unidades.list_candidatas_por_condado(
            idcondado, idcondados_extra=vecinos if incluir_vecinos else None
        )
        rechazadas = self._unidades_rechazaron(idaccidente)
        excluir = set(excluir_unidades or set()) | rechazadas
        params = self.parametros.get()
        lat_acc = float(accidente["latitudinicio"])
        lon_acc = float(accidente["longitudinicio"])
        resultados: list[dict[str, Any]] = []
        for unidad in candidatas:
            uid = int(unidad["idunidademergencia"])
            if uid in excluir:
                continue
            estado, desde_ms = self.historial_unidad.get_current_estado(uid)
            if estado != ESTADO_ACTIVA:
                continue
            if self.despachos.has_active_for_unidad(uid):
                continue
            pos = self.ubicacion.posicion_efectiva(uid)
            if not pos:
                continue
            dist = haversine_km(lat_acc, lon_acc, pos["latitud"], pos["longitud"])
            dist_score = max(0.0, 1.0 - min(dist / 50.0, 1.0))
            tipo_score = self.concordancia.score_tipo(
                idseveridad=int(accidente.get("idseveridad", 1)),
                tipounidademergencia=str(unidad.get("tipounidademergencia", "")),
                descripcion=accidente.get("descripcion"),
            )
            disp_score = self._disponibilidad_reciente_score(desde_ms)
            peso_d = params["peso_distancia_pct"] / 100.0
            peso_c = params["peso_concordancia_pct"] / 100.0
            peso_a = params["peso_disponibilidad_pct"] / 100.0
            puntuacion = (dist_score * peso_d) + (tipo_score * peso_c) + (disp_score * peso_a)
            resultados.append(
                {
                    "idunidademergencia": uid,
                    "unidademergencia": unidad.get("unidademergencia"),
                    "tipounidademergencia": unidad.get("tipounidademergencia"),
                    "distancia_km": round(dist, 2),
                    "puntuacion": round(puntuacion, 4),
                    "estado_unidad": ESTADO_ACTIVA,
                    "eta_minutos": max(1, int(dist * 2)),
                }
            )
        resultados.sort(key=lambda r: r["puntuacion"], reverse=True)
        return resultados

    @staticmethod
    def _disponibilidad_reciente_score(desde_ms: int | None) -> float:
        """RN-DES-008: mayor puntuación a unidades con más tiempo continuo en estado Activa."""
        if not desde_ms:
            return 0.0
        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        minutos_activa = max(0.0, (now_ms - desde_ms) / 60000.0)
        return min(minutos_activa / DISPONIBILIDAD_MAX_MINUTOS, 1.0)

    def _unidades_rechazaron(self, idaccidente: str) -> set[int]:
        rechazadas: set[int] = set()
        for notif in self.notificaciones.list_by_accidente(idaccidente):
            if notif.get("estadonotificaciondespacho") == ESTADO_RECHAZADA:
                rechazadas.add(int(notif["idunidaddemergencia"]))
        return rechazadas
