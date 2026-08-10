"""Dim_Partner repository — nucleo del departamento (CU-O48).

Escritura exclusiva via Kafka; Pinot es solo lectura.

CENTINELAS, NO NULL: Pinot no almacena nulos en este proyecto. Un partner sin
plan lleva `planapi = ""` (no `'null'`, que era el centinela implicito de Pinot
y hacia que la guarda "no es nulo" fuera siempre cierta). Ver
`partner-api-onboarding/backend/spec.md` seccion 15 D2.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from django.conf import settings

from apps.partners.domain_constants import (
    SIN_CUPO,
    SIN_ACTIVACION,
    SIN_PLAN,
    SIN_SUSPENSION,
)
from core.pinot.client import PinotClient
from core.repositories.partners.kafka_writer import KafkaWriter


class PartnerRepository:
    TOPIC = settings.KAFKA_TOPICS["partner"]

    def __init__(self, pinot: PinotClient | None = None, kafka: KafkaWriter | None = None):
        self.pinot = pinot or PinotClient()
        self.kafka = kafka or KafkaWriter()

    @staticmethod
    def _now_ms() -> int:
        return int(datetime.now(timezone.utc).timestamp() * 1000)

    def _next_id(self) -> int:
        rows = self.pinot.query("SELECT MAX(idpartner) AS max_id FROM Dim_Partner LIMIT 1", {})
        return int(rows[0]["max_id"] or 0) + 1 if rows else 1

    # --- Lecturas -----------------------------------------------------------

    def find_by_id(self, idpartner: int) -> dict[str, Any] | None:
        rows = self.pinot.query(
            "SELECT * FROM Dim_Partner WHERE idpartner = %(idpartner)s LIMIT 1",
            {"idpartner": idpartner},
        )
        return rows[0] if rows else None

    def find_by_cliente(self, idcliente: int) -> dict[str, Any] | None:
        """RN-PON-002 — un cliente tiene un unico perfil de partner.

        Pinot no soporta UNIQUE, asi que la unicidad se valida a nivel de
        aplicacion consultando aqui antes de insertar.
        """
        rows = self.pinot.query(
            "SELECT * FROM Dim_Partner WHERE idcliente = %(idcliente)s LIMIT 1",
            {"idcliente": idcliente},
        )
        return rows[0] if rows else None

    def list(self, *, limit: int = 20, cursor: int | None = None) -> tuple[list[dict], int | None]:
        """Listado paginado por cursor (api-standards.md).

        El LIMIT es explicito a proposito: Pinot aplica `LIMIT 10` implicito y
        silencioso a toda consulta sin el.
        """
        params: dict[str, Any] = {"limit": limit + 1}
        where = ""
        if cursor is not None:
            where = "WHERE idpartner < %(cursor)s "
            params["cursor"] = cursor
        rows = self.pinot.query(
            f"SELECT * FROM Dim_Partner {where}ORDER BY idpartner DESC LIMIT %(limit)s",
            params,
        )
        next_cursor = rows[limit]["idpartner"] if len(rows) > limit else None
        return rows[:limit], next_cursor

    # --- Escrituras (via Kafka) ---------------------------------------------

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        """RF-PON-001 — el partner nace sin plan ni cupo.

        Los centinelas son explicitos: nunca se publica `None`, porque Pinot lo
        convertiria en un valor que rompe las guardas del modulo.
        """
        now = self._now_ms()
        fila = {
            "idpartner": data.get("idpartner") or self._next_id(),
            "idcliente": int(data["idcliente"]),
            "nombrepartner": data["nombrepartner"],
            "contacto_tecnico_nombre": data["contacto_tecnico_nombre"],
            "contacto_tecnico_gmail": data["contacto_tecnico_gmail"],
            "planapi": SIN_PLAN,
            "limitellamadasmes": SIN_CUPO,
            "limitellamadasminuto": SIN_CUPO,
            "sandbox_activado": SIN_ACTIVACION,
            "sandbox_expiracion": SIN_ACTIVACION,
            "fecha_suspension": SIN_SUSPENSION,
            "motivo_suspension": SIN_SUSPENSION,
            "activo": True,
            "fecha_actualizacion": now,
        }
        self.kafka.publish(self.TOPIC, fila)
        return fila

    def update(self, idpartner: int, changes: dict[str, Any]) -> dict[str, Any] | None:
        """Upsert FULL: se republica la fila COMPLETA.

        Publicar solo los campos cambiados borraria el resto (upsert por PK).
        `fecha_actualizacion` debe avanzar siempre: es el `comparisonColumn`.
        """
        actual = self.find_by_id(idpartner)
        if not actual:
            return None
        fila = {**actual, **changes, "fecha_actualizacion": self._now_ms()}
        self.kafka.publish(self.TOPIC, fila)
        return fila
