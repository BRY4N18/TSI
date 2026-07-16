"""Consultas mi-despacho para unidad de emergencia."""

from __future__ import annotations

from typing import Any

from apps.despacho.services.consulta_candidatas_service import ConsultaCandidatasService
from core.repositories.accidentes.accidente_repository import AccidenteRepository
from core.repositories.despacho.notificacion_despacho_repository import (
    ESTADO_CONFIRMADA,
    ESTADO_NOTIFICADA,
    ESTADO_PENDIENTE,
    ESTADO_RECHAZADA,
    NotificacionDespachoRepository,
)
from core.repositories.despacho.unidad_emergencia_repository import UnidadEmergenciaRepository

PENDIENTES = {ESTADO_PENDIENTE, ESTADO_NOTIFICADA}
SEVERIDAD_LABELS = {1: "Leve", 2: "Moderada", 3: "Grave", 4: "Crítica"}


class MiDespachoService:
    def __init__(
        self,
        notificacion_repo: NotificacionDespachoRepository | None = None,
        unidad_repo: UnidadEmergenciaRepository | None = None,
        accidente_repo: AccidenteRepository | None = None,
        candidatas: ConsultaCandidatasService | None = None,
    ):
        self.notificaciones = notificacion_repo or NotificacionDespachoRepository()
        self.unidades = unidad_repo or UnidadEmergenciaRepository()
        self.accidentes = accidente_repo or AccidenteRepository()
        self.candidatas = candidatas or ConsultaCandidatasService()

    def listar_pendientes(self, *, idusuario: int) -> list[dict[str, Any]]:
        unidad = self.unidades.find_by_usuario(idusuario)
        if not unidad:
            raise LookupError("Unidad no vinculada")
        idunidad = int(unidad["idunidademergencia"])
        pendientes: list[dict[str, Any]] = []
        for notif in self.notificaciones.list_by_unidad(idunidad):
            estado = notif.get("estadonotificaciondespacho")
            if estado not in PENDIENTES:
                continue
            item = self._map_pendiente(notif, unidad)
            if item:
                pendientes.append(item)
        return pendientes

    def obtener_detalle(
        self, *, idnotificaciondespacho: int, idunidademergencia: int
    ) -> dict[str, Any]:
        notif = self.notificaciones.find_by_id(idnotificaciondespacho)
        if not notif:
            raise LookupError("Notificación no encontrada")
        if int(notif["idunidaddemergencia"]) != idunidademergencia:
            raise PermissionError("Notificación no pertenece a la unidad")
        unidad = self.unidades.find_by_id(idunidademergencia)
        item = self._map_pendiente(notif, unidad or {"idunidademergencia": idunidademergencia})
        if not item:
            raise LookupError("Notificación no encontrada")
        return item

    def _map_pendiente(
        self, notif: dict[str, Any], unidad: dict[str, Any]
    ) -> dict[str, Any] | None:
        idunidad = int(unidad["idunidademergencia"])
        idaccidente = notif["idaccidente"]
        accidente = self.accidentes.find_by_id(idaccidente)
        if not accidente:
            return None
        idseveridad = int(accidente.get("idseveridad", 1))
        eta = self._eta_minutos(idaccidente, idunidad)
        return {
            "idnotificaciondespacho": notif["idnotificaciondespacho"],
            "idaccidente": idaccidente,
            "idseveridad": idseveridad,
            "severidad": SEVERIDAD_LABELS.get(idseveridad, "Desconocida"),
            "estadonotificacion": notif.get("estadonotificaciondespacho"),
            "descripcion": accidente.get("descripcion"),
            "direccion_aproximada": accidente.get("direccion") or "Ubicación aproximada",
            "latitud": float(accidente["latitudinicio"]),
            "longitud": float(accidente["longitudinicio"]),
            "eta_minutos": eta,
            "fechahora": notif.get("fecha_actualizacion", accidente.get("fechahoraaccidente")),
            "idunidademergencia": idunidad,
            "unidademergencia": unidad.get("unidademergencia", ""),
            "unidad_latitud": float(unidad["latitud"]) if unidad.get("latitud") is not None else None,
            "unidad_longitud": float(unidad["longitud"]) if unidad.get("longitud") is not None else None,
        }

    def _eta_minutos(self, idaccidente: str, idunidad: int) -> int:
        try:
            ranked = self.candidatas.listar_puntuadas(idaccidente)
            for row in ranked:
                if row["idunidademergencia"] == idunidad:
                    return int(row.get("eta_minutos", 5))
        except LookupError:
            pass
        return 5
