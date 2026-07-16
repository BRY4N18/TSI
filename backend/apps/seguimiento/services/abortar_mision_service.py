"""CU-O39 — abortar misión en tránsito."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from django.conf import settings

from core.repositories.accidentes.kafka_writer import KafkaWriter
from core.repositories.despacho.despacho_repository import DespachoRepository
from core.repositories.despacho.historial_despacho_repository import (
    ESTADO_ABORTADO,
    ESTADO_CONFIRMADO,
    HistorialDespachoRepository,
)
from core.repositories.despacho.historial_estado_unidad_repository import (
    ESTADO_ACTIVA,
    ESTADO_FUERA_SERVICIO,
    HistorialEstadoUnidadRepository,
)


class AbortarMisionService:
    TOPIC = settings.KAFKA_TOPICS["despacho_abortado"]

    def __init__(
        self,
        despacho_repo: DespachoRepository | None = None,
        historial_repo: HistorialDespachoRepository | None = None,
        historial_unidad: HistorialEstadoUnidadRepository | None = None,
        kafka: KafkaWriter | None = None,
    ):
        self.despachos = despacho_repo or DespachoRepository()
        self.historial = historial_repo or HistorialDespachoRepository()
        self.historial_unidad = historial_unidad or HistorialEstadoUnidadRepository()
        self.kafka = kafka or KafkaWriter()

    def abortar(
        self,
        *,
        iddespacho: int,
        idunidademergencia: int,
        idusuario: int,
        motivo: str | None = None,
    ) -> dict[str, Any]:
        despacho = self.despachos.find_by_id(iddespacho)
        if not despacho:
            raise LookupError("Despacho no encontrado")
        if int(despacho["idunidademergencia"]) != idunidademergencia:
            raise PermissionError("Despacho no pertenece a la unidad")
        estado, _ = self.historial.get_current_estado(iddespacho)
        if estado != ESTADO_CONFIRMADO:
            raise ValueError(f"Estado inválido para abortar: {estado}")

        self.historial.publish(
            iddespacho=iddespacho,
            estadonuevo=ESTADO_ABORTADO,
            idusuario=idusuario,
        )
        self.despachos.publish_update(iddespacho, {"activo": False})
        estado_unidad_actual, _ = self.historial_unidad.get_current_estado(idunidademergencia)
        estado_unidad_destino = (
            ESTADO_FUERA_SERVICIO
            if estado_unidad_actual == ESTADO_FUERA_SERVICIO
            else ESTADO_ACTIVA
        )
        self.historial_unidad.append_estado(
            idunidademergencia=idunidademergencia,
            estadonuevo=estado_unidad_destino,
            idusuario=idusuario,
        )
        event = {
            "iddespacho": iddespacho,
            "idaccidente": despacho["idaccidente"],
            "idunidademergencia": idunidademergencia,
            "idusuario": idusuario,
            "motivo": motivo,
            "fechahora": int(datetime.now(timezone.utc).timestamp() * 1000),
        }
        self.kafka.publish(self.TOPIC, event)

        return {
            "iddespacho": iddespacho,
            "idaccidente": despacho["idaccidente"],
            "estado_despacho": ESTADO_ABORTADO,
            "estado_unidad": estado_unidad_destino,
            "reasignacion_disparada": True,
        }
