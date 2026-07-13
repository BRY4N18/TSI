"""RF-DES-011 — monitoreo de despacho y SSE pub/sub."""

from __future__ import annotations

import json
import queue
import threading
import time
from datetime import datetime, timezone
from typing import Any, Iterator

from apps.accidentes.domain_constants import ESTADO_ASIGNADO, ESTADO_BUSCANDO_UNIDAD
from core.repositories.accidentes.accidente_repository import AccidenteRepository
from core.repositories.accidentes.estado_accidente_repository import EstadoAccidenteRepository
from apps.despacho.services.asignacion_inteligente_service import ORIGEN_IDS
from core.repositories.despacho.despacho_repository import DespachoRepository

ORIGEN_NAMES: dict[int, str] = {v: k for k, v in ORIGEN_IDS.items()}
from core.repositories.despacho.historial_despacho_repository import HistorialDespachoRepository
from core.repositories.despacho.notificacion_despacho_repository import NotificacionDespachoRepository
from core.repositories.despacho.unidad_emergencia_repository import UnidadEmergenciaRepository


class DespachoSseBroker:
    _lock = threading.Lock()
    _channels: dict[str, list[queue.Queue[str]]] = {}

    @classmethod
    def subscribe(cls, idaccidente: str) -> queue.Queue[str]:
        q: queue.Queue[str] = queue.Queue()
        with cls._lock:
            cls._channels.setdefault(idaccidente, []).append(q)
        return q

    @classmethod
    def publish(cls, idaccidente: str, payload: dict[str, Any]) -> None:
        data = json.dumps(payload, ensure_ascii=False)
        frame = f"event: despacho.actualizado\ndata: {data}\n\n"
        with cls._lock:
            channels = list(cls._channels.get(idaccidente, []))
        for q in channels:
            q.put(frame)

    @classmethod
    def unsubscribe(cls, idaccidente: str, q: queue.Queue[str]) -> None:
        with cls._lock:
            subs = cls._channels.get(idaccidente, [])
            if q in subs:
                subs.remove(q)


class MonitoreoDespachoService:
    def __init__(
        self,
        accidente_repo: AccidenteRepository | None = None,
        estado_repo: EstadoAccidenteRepository | None = None,
        despacho_repo: DespachoRepository | None = None,
        historial_repo: HistorialDespachoRepository | None = None,
        notificacion_repo: NotificacionDespachoRepository | None = None,
        unidad_repo: UnidadEmergenciaRepository | None = None,
    ):
        self.accidentes = accidente_repo or AccidenteRepository()
        self.estado = estado_repo or EstadoAccidenteRepository()
        self.despachos = despacho_repo or DespachoRepository()
        self.historial = historial_repo or HistorialDespachoRepository()
        self.notificaciones = notificacion_repo or NotificacionDespachoRepository()
        self.unidades = unidad_repo or UnidadEmergenciaRepository()

    def obtener_estado(self, idaccidente: str) -> dict[str, Any]:
        if not self.accidentes.find_by_id(idaccidente):
            raise LookupError("Accidente no encontrado")
        accidente = self.accidentes.find_by_id(idaccidente)
        assert accidente is not None
        inicio = int(accidente.get("fechahoraaccidente", 0))
        now = int(datetime.now(timezone.utc).timestamp() * 1000)
        estado_caso = self.estado.get_current_estado(idaccidente) or ESTADO_BUSCANDO_UNIDAD
        intentos = self._build_intentos(idaccidente)
        activos = [i for i in intentos if i["activo"]]
        mensaje = (
            "Buscando unidad..."
            if estado_caso == ESTADO_BUSCANDO_UNIDAD
            else "Unidad asignada"
        )
        return {
            "idaccidente": idaccidente,
            "estado_caso": estado_caso,
            "tiempo_transcurrido_seg": max(0, (now - inicio) // 1000),
            "intentos": intentos,
            "unidades_activas": activos,
            "mensaje": mensaje,
        }

    def notificar_actualizacion(self, idaccidente: str) -> None:
        data = self.obtener_estado(idaccidente)
        DespachoSseBroker.publish(
            idaccidente,
            {
                "idaccidente": data["idaccidente"],
                "estado_caso": data["estado_caso"],
                "intentos": len(data["intentos"]),
            },
        )

    def stream_eventos(
        self, idaccidente: str, *, timeout_sec: float = 30.0
    ) -> Iterator[str]:
        if not self.accidentes.find_by_id(idaccidente):
            raise LookupError("Accidente no encontrado")
        q = DespachoSseBroker.subscribe(idaccidente)
        try:
            yield f"event: despacho.snapshot\ndata: {json.dumps(self.obtener_estado(idaccidente), ensure_ascii=False)}\n\n"
            deadline = time.monotonic() + timeout_sec
            while time.monotonic() < deadline:
                try:
                    frame = q.get(timeout=1.0)
                    yield frame
                except queue.Empty:
                    yield ": heartbeat\n\n"
        finally:
            DespachoSseBroker.unsubscribe(idaccidente, q)

    def _build_intentos(self, idaccidente: str) -> list[dict[str, Any]]:
        intentos: list[dict[str, Any]] = []
        for despacho in self.despachos.list_by_accidente(idaccidente):
            estado, _ = self.historial.get_current_estado(despacho["iddespacho"])
            unidad = self.unidades.find_by_id(int(despacho["idunidademergencia"]))
            notif_estado = None
            motivo = None
            idnotif = despacho.get("idnotificaciondespacho")
            if idnotif is not None:
                notif = self.notificaciones.find_by_id(int(idnotif))
                if notif:
                    notif_estado = notif.get("estadonotificaciondespacho")
                    motivo = notif.get("motivo")
            intentos.append(
                {
                    "iddespacho": despacho["iddespacho"],
                    "idunidademergencia": despacho["idunidademergencia"],
                    "unidademergencia": (unidad or {}).get("unidademergencia", ""),
                    "tipounidademergencia": (unidad or {}).get("tipounidademergencia", ""),
                    "estado": estado,
                    "estadonotificacion": notif_estado,
                    "motivo": motivo,
                    "origen": ORIGEN_NAMES.get(despacho.get("idorigendespacho"), "Automatico"),
                    "fechahoradespacho": despacho.get("fechahoradespacho"),
                    "activo": bool(despacho.get("activo")),
                }
            )
        return intentos
