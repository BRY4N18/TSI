"""Dim_SLAConfig repository — versionado temporal (CU-O95, RN-TIC-006)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from django.conf import settings

from core.pinot.client import PinotClient
from core.repositories.soporte.kafka_writer import KafkaWriter


class SLAConfigRepository:
    TOPIC = settings.KAFKA_TOPICS["sla_config"]

    def __init__(self, pinot: PinotClient | None = None, kafka: KafkaWriter | None = None):
        self.pinot = pinot or PinotClient()
        self.kafka = kafka or KafkaWriter()

    def _next_id(self) -> int:
        rows = self.pinot.query("SELECT MAX(idslaconfig) AS max_id FROM Dim_SLAConfig", {})
        return int(rows[0]["max_id"] or 0) + 1 if rows else 1

    def list(self) -> list[dict[str, Any]]:
        return self.pinot.query("SELECT * FROM Dim_SLAConfig", {})

    def find_by_id(self, idslaconfig: int) -> dict[str, Any] | None:
        rows = self.pinot.query(
            "SELECT * FROM Dim_SLAConfig WHERE idslaconfig = %(idslaconfig)s",
            {"idslaconfig": idslaconfig},
        )
        return rows[0] if rows else None

    def find_vigente(
        self, *, idplan: int, tipoincidencia: str, prioridad: str
    ) -> dict[str, Any] | None:
        rows = self.list()
        candidatos = [
            r
            for r in rows
            if r.get("activo")
            and r.get("idplan") == idplan
            and r.get("tipoincidencia") == tipoincidencia
            and r.get("prioridad") == prioridad
        ]
        return candidatos[0] if candidatos else None

    def crear_regla(
        self,
        *,
        idplan: int,
        tipoincidencia: str,
        prioridad: str,
        tiemporespuestamax: int,
        tiemporesolucionmax: int,
    ) -> dict[str, Any]:
        now = int(datetime.now(timezone.utc).timestamp() * 1000)
        payload = {
            "idslaconfig": self._next_id(),
            "idplan": idplan,
            "tipoincidencia": tipoincidencia,
            "prioridad": prioridad,
            "activo": True,
            "tiemporespuestamax": tiemporespuestamax,
            "tiemporesolucionmax": tiemporesolucionmax,
            "fechavigenciadesde": now,
            "fechavigenciahasta": None,
            "fecha_actualizacion": now,
        }
        self.kafka.publish(self.TOPIC, payload)
        return payload

    def desactivar(self, idslaconfig: int) -> dict[str, Any]:
        current = self.find_by_id(idslaconfig)
        if not current:
            raise LookupError(f"Configuración SLA {idslaconfig} no encontrada")
        now = int(datetime.now(timezone.utc).timestamp() * 1000)
        record = {
            **current,
            "activo": False,
            "fechavigenciahasta": now,
            "fecha_actualizacion": now,
        }
        self.kafka.publish(self.TOPIC, record)
        return record

    def modificar_regla(
        self,
        idslaconfig: int,
        *,
        tiemporespuestamax: int,
        tiemporesolucionmax: int,
    ) -> dict[str, Any]:
        """Cierra la vigencia de la regla actual e inserta una nueva fila (RF-TIC-003)."""
        actual = self.find_by_id(idslaconfig)
        if not actual:
            raise LookupError(f"Configuración SLA {idslaconfig} no encontrada")
        self.desactivar(idslaconfig)
        return self.crear_regla(
            idplan=actual["idplan"],
            tipoincidencia=actual["tipoincidencia"],
            prioridad=actual["prioridad"],
            tiemporespuestamax=tiemporespuestamax,
            tiemporesolucionmax=tiemporesolucionmax,
        )
