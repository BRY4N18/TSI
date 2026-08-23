"""Dim_VersionContratoAPI repository — contrato versionado POR SERVICIO (CU-O50).

La FK `id_servicio` es obligatoria: `Dim_Servicio` contiene varios servicios
(API Despacho, API Registro de accidentes, Portal Cliente) y cada uno lleva su
propio ciclo de versionado. Sin la FK, los tres colapsarian en una sola linea
temporal. Ver `spec.md` seccion 15 D1.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from django.conf import settings

from apps.partners.domain_constants import (
    SIN_FECHA_RETIRO,
    SIN_URL,
    VERSION_VIGENTE,
)
from core.pinot.client import PinotClient
from core.repositories.partners.kafka_writer import KafkaWriter
from core.pinot.secuencia import siguiente_id


class VersionContratoRepository:
    TOPIC = settings.KAFKA_TOPICS["version_contrato_api"]

    def __init__(self, pinot: PinotClient | None = None, kafka: KafkaWriter | None = None):
        self.pinot = pinot or PinotClient()
        self.kafka = kafka or KafkaWriter()

    @staticmethod
    def _now_ms() -> int:
        return int(datetime.now(timezone.utc).timestamp() * 1000)

    def _next_id(self) -> int:
        return siguiente_id(self.pinot, "Dim_VersionContratoAPI", "idversion")

    # --- Lecturas -----------------------------------------------------------

    def list_by_servicio(self, id_servicio: int) -> list[dict[str, Any]]:
        return self.pinot.query(
            "SELECT * FROM Dim_VersionContratoAPI WHERE id_servicio = %(id_servicio)s "
            "AND activo = true ORDER BY fecha_publicacion DESC LIMIT 100",
            {"id_servicio": id_servicio},
        )

    def vigente(self, id_servicio: int) -> dict[str, Any] | None:
        """La version vigente del servicio. Como maximo una (RF-PON-011)."""
        for v in self.list_by_servicio(id_servicio):
            if v.get("estado") == VERSION_VIGENTE:
                return v
        return None

    def find_version(self, id_servicio: int, version: str) -> dict[str, Any] | None:
        for v in self.list_by_servicio(id_servicio):
            if v.get("version") == version:
                return v
        return None

    # --- Escritura ----------------------------------------------------------

    def upsert(self, data: dict[str, Any]) -> dict[str, Any]:
        now = self._now_ms()
        fila = {
            "idversion": data.get("idversion") or self._next_id(),
            "id_servicio": int(data["id_servicio"]),
            "version": data["version"],
            "estado": data["estado"],
            "spec_url": data.get("spec_url", SIN_URL),
            "fecha_publicacion": data.get("fecha_publicacion", now),
            "fecha_retiro": data.get("fecha_retiro", SIN_FECHA_RETIRO),
            "activo": data.get("activo", True),
            "fecha_actualizacion": now,
        }
        self.kafka.publish(self.TOPIC, fila)
        return fila
