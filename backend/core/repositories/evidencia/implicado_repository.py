"""Dim_Implicado repository — Pinot read, Kafka write (CU-O46 / RF-EVI-010).

Payload alineado a ontología / database/esquemas.json (Decision 13).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from django.conf import settings

from core.pinot.client import PinotClient
from core.repositories.accidentes.kafka_writer import KafkaWriter

TIPOS_IMPLICADO = frozenset({"Peaton", "Pasajero", "Testigo", "Otro"})
ESTADOS_IMPLICADO = frozenset({"Ileso", "Lesionado", "Fallecido", "Desconocido"})

# Keys de negocio + auditoría infra ( ⊆ Dim_Implicado schema Pinot )
PAYLOAD_KEYS = frozenset(
    {
        "idimplicado",
        "idaccidente",
        "tipoimplicado",
        "genero",
        "estadoimplicado",
        "edad",
        "activo",
        "fecha_actualizacion",
    }
)


class ImplicadoRepository:
    TOPIC = settings.KAFKA_TOPICS["implicado"]

    def __init__(
        self,
        pinot: PinotClient | None = None,
        kafka: KafkaWriter | None = None,
    ):
        self.pinot = pinot or PinotClient()
        self.kafka = kafka or KafkaWriter()

    def _next_id(self) -> int:
        rows = self.pinot.query(
            "SELECT MAX(idimplicado) AS max_id FROM Dim_Implicado",
            {},
        )
        return int(rows[0]["max_id"] or 0) + 1 if rows else 1

    def find_by_id(self, idimplicado: int) -> dict[str, Any] | None:
        rows = self.pinot.query(
            """
            SELECT * FROM Dim_Implicado
            WHERE idimplicado = %(id)s
            LIMIT 1
            """,
            {"id": idimplicado},
        )
        return rows[0] if rows else None

    def list_activos_by_accidente(self, idaccidente: str) -> list[dict[str, Any]]:
        rows = self.pinot.query(
            """
            SELECT * FROM Dim_Implicado
            WHERE idaccidente = %(idaccidente)s
            """,
            {"idaccidente": idaccidente},
        )
        return [r for r in rows if r.get("activo", True)]

    def create(
        self,
        *,
        idaccidente: str,
        tipoimplicado: str,
        estadoimplicado: str,
        genero: str | None = None,
        edad: int | None = None,
    ) -> dict[str, Any]:
        now = int(datetime.now(timezone.utc).timestamp() * 1000)
        payload = {
            "idimplicado": self._next_id(),
            "idaccidente": idaccidente,
            "tipoimplicado": tipoimplicado,
            "genero": genero,
            "estadoimplicado": estadoimplicado,
            "edad": edad,
            "activo": True,
            "fecha_actualizacion": now,
        }
        self.kafka.publish(self.TOPIC, payload)
        return payload

    def soft_delete(self, *, idimplicado: int) -> dict[str, Any] | None:
        current = self.find_by_id(idimplicado)
        if not current:
            return None
        now = int(datetime.now(timezone.utc).timestamp() * 1000)
        payload = {
            "idimplicado": current["idimplicado"],
            "idaccidente": current["idaccidente"],
            "tipoimplicado": current.get("tipoimplicado"),
            "genero": current.get("genero"),
            "estadoimplicado": current.get("estadoimplicado"),
            "edad": current.get("edad"),
            "activo": False,
            "fecha_actualizacion": now,
        }
        self.kafka.publish(self.TOPIC, payload)
        return payload
