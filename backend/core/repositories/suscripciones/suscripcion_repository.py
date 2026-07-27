"""Fact_Suscripcion repository canónico — lectura/escritura Kafka (Title Case)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo

from dateutil.relativedelta import relativedelta
from django.conf import settings

from core.pinot.client import PinotClient
from core.repositories.suscripciones.kafka_writer import KafkaWriter

TZ = ZoneInfo("America/Guayaquil")
ESTADOS = frozenset({"Activa", "Suspendida", "Cancelada"})


class SuscripcionRepository:
    TOPIC = settings.KAFKA_TOPICS["suscripcion"]

    def __init__(self, pinot: PinotClient | None = None, kafka: KafkaWriter | None = None):
        self.pinot = pinot or PinotClient()
        self.kafka = kafka or KafkaWriter()

    def _now_ms(self) -> int:
        return int(datetime.now(timezone.utc).timestamp() * 1000)

    def _next_id(self) -> int:
        rows = self.pinot.query("SELECT MAX(id_suscripcion) AS max_id FROM Fact_Suscripcion", {})
        return int(rows[0]["max_id"] or 0) + 1 if rows else 1

    @staticmethod
    def add_calendar_month(dt: datetime) -> datetime:
        return dt + relativedelta(months=1)

    def find_by_id(self, id_suscripcion: int) -> dict[str, Any] | None:
        rows = self.pinot.query(
            "SELECT * FROM Fact_Suscripcion WHERE id_suscripcion = %(id)s",
            {"id": id_suscripcion},
        )
        return rows[0] if rows else None

    def find_activa_by_cliente(self, idcliente: int) -> dict[str, Any] | None:
        rows = list(self.pinot.query("SELECT * FROM Fact_Suscripcion", {}) or [])
        candidates = [
            r
            for r in rows
            if r.get("idcliente") == idcliente and r.get("activo") is True
        ]
        if not candidates:
            return None
        candidates.sort(key=lambda r: r.get("fecha_inicio") or 0, reverse=True)
        return candidates[0]

    def list_elegibles_facturacion(self) -> list[dict[str, Any]]:
        rows = list(self.pinot.query("SELECT * FROM Fact_Suscripcion", {}) or [])
        return [r for r in rows if r.get("activo") and r.get("estado") == "Activa"]

    def list_elegibles_renovacion(self, *, now: datetime | None = None) -> list[dict[str, Any]]:
        now = now or datetime.now(TZ)
        out = []
        for r in self.list_elegibles_facturacion():
            if not r.get("renovacionautomatica"):
                continue
            fecha_fin = r.get("fecha_fin")
            if fecha_fin is None:
                continue
            # Accept ms epoch or ISO
            if isinstance(fecha_fin, (int, float)):
                fin_dt = datetime.fromtimestamp(fecha_fin / 1000, tz=TZ)
            else:
                fin_dt = datetime.fromisoformat(str(fecha_fin).replace("Z", "+00:00")).astimezone(TZ)
            if fin_dt <= now:
                out.append(r)
        return out

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        now = datetime.now(TZ)
        fecha_fin = self.add_calendar_month(now)
        record = {
            "id_suscripcion": self._next_id(),
            "idcliente": data["idcliente"],
            "idplan": data["idplan"],
            "precio": float(data["precio"]),
            "estado": "Activa",
            "activo": True,
            "renovacionautomatica": bool(data.get("renovacionautomatica", True)),
            "motivocancelacion": None,
            "fechacancelacion": None,
            "fecha_inicio": int(now.timestamp() * 1000),
            "fecha_fin": int(fecha_fin.timestamp() * 1000),
            "fecha_actualizacion": self._now_ms(),
        }
        self.kafka.publish(self.TOPIC, record)
        return record

    def update(self, id_suscripcion: int, changes: dict[str, Any]) -> dict[str, Any] | None:
        current = self.find_by_id(id_suscripcion)
        if not current:
            return None
        if "estado" in changes and changes["estado"] not in ESTADOS:
            raise ValueError(f"estado inválido: {changes['estado']}")
        payload = {**current, **changes, "fecha_actualizacion": self._now_ms()}
        self.kafka.publish(self.TOPIC, payload)
        return payload

    def cancelar(
        self,
        id_suscripcion: int,
        *,
        motivocancelacion: str = "",
    ) -> dict[str, Any] | None:
        """Marca Cancelada manteniendo activo=true hasta fecha_fin (RN-017 / RF-SUSF-009)."""
        current = self.find_by_id(id_suscripcion)
        if not current:
            return None
        return self.update(
            id_suscripcion,
            {
                "estado": "Cancelada",
                "motivocancelacion": motivocancelacion or None,
                "fechacancelacion": self._now_ms(),
                # activo permanece True hasta job de mantenimiento post fecha_fin
                "activo": True,
                "renovacionautomatica": False,
            },
        )
