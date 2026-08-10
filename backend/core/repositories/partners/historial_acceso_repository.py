"""Fact_HistorialAccesoPartner repository — bitacora inmutable (RF-PON-010).

SOLO INSERT. Esta clase NO expone `update` ni `delete` a proposito: la
inmutabilidad de la bitacora no es una convencion que se recuerde, es una
capacidad que no existe (RN-PON-010).

Ademas de auditoria, es la fuente operativa de la reactivacion selectiva de
#09: las filas `desactivacion_por_cascada` son las que se restituyen.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from django.conf import settings

from apps.partners.domain_constants import SIN_CREDENCIAL, SIN_MOTIVO
from core.pinot.client import PinotClient
from core.repositories.partners.kafka_writer import KafkaWriter


class HistorialAccesoRepository:
    TOPIC = settings.KAFKA_TOPICS["historial_acceso_partner"]

    def __init__(self, pinot: PinotClient | None = None, kafka: KafkaWriter | None = None):
        self.pinot = pinot or PinotClient()
        self.kafka = kafka or KafkaWriter()

    @staticmethod
    def _now_ms() -> int:
        return int(datetime.now(timezone.utc).timestamp() * 1000)

    def _next_id(self) -> int:
        rows = self.pinot.query(
            "SELECT MAX(idhistorial) AS max_id FROM Fact_HistorialAccesoPartner LIMIT 1", {}
        )
        return int(rows[0]["max_id"] or 0) + 1 if rows else 1

    # --- Lecturas -----------------------------------------------------------

    def list_by_partner(self, idpartner: int, *, limit: int = 200) -> list[dict[str, Any]]:
        return self.pinot.query(
            # Desempate por idhistorial: dos eventos del mismo flujo pueden caer
            # en el mismo milisegundo, y entonces `fecha_cambio` sola no basta
            # para saber cual es el ultimo.
            "SELECT * FROM Fact_HistorialAccesoPartner WHERE idpartner = %(idpartner)s "
            "ORDER BY fecha_cambio DESC, idhistorial DESC LIMIT %(limit)s",
            {"idpartner": idpartner, "limit": limit},
        )

    def ultimo_evento(self, idpartner: int) -> dict[str, Any] | None:
        eventos = self.list_by_partner(idpartner, limit=1)
        return eventos[0] if eventos else None

    def existe_evento(
        self,
        idpartner: int,
        tipo_cambio: str,
        *,
        motivo: str | None = None,
        desde_ms: int | None = None,
    ) -> bool:
        """Para las reglas de no duplicacion (avisos de vencimiento y de mora)."""
        for ev in self.list_by_partner(idpartner, limit=500):
            if ev.get("tipo_cambio") != tipo_cambio:
                continue
            if motivo is not None and ev.get("motivo") != motivo:
                continue
            if desde_ms is not None and int(ev.get("fecha_cambio", 0)) < desde_ms:
                continue
            return True
        return False

    # --- Escritura (solo INSERT) --------------------------------------------

    def registrar(
        self,
        *,
        idpartner: int,
        tipo_cambio: str,
        ejecutado_por: str,
        estado_nuevo: str,
        estado_anterior: str = SIN_MOTIVO,
        motivo: str = SIN_MOTIVO,
        idcredencial: int = SIN_CREDENCIAL,
    ) -> dict[str, Any]:
        """Inserta un evento. Nunca actualiza: cada evento es una fila nueva.

        `idcredencial` vale el centinela -1 cuando el evento es sobre el partner
        en general (registro, plan, solicitud, aprobacion, rechazo) y lleva el id
        real cuando afecta a una credencial concreta (emision, expiracion).
        """
        fila = {
            "idhistorial": self._next_id(),
            "idpartner": int(idpartner),
            "idcredencial": int(idcredencial),
            "tipo_cambio": tipo_cambio,
            "ejecutado_por": ejecutado_por,
            "motivo": motivo,
            "estado_anterior": estado_anterior,
            "estado_nuevo": estado_nuevo,
            "fecha_cambio": self._now_ms(),
            "fecha_actualizacion": self._now_ms(),
        }
        self.kafka.publish(self.TOPIC, fila)
        return fila
