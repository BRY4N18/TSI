"""Fact_Factura repository — RF-SUSF-004/005 (seq RN-026)."""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

from django.conf import settings

from core.pinot.client import PinotClient
from core.repositories.suscripciones.kafka_writer import KafkaWriter

TZ = ZoneInfo("America/Guayaquil")
_SEQ_RE = re.compile(r"^FAC-(\d{6})-(\d{8})$")


class FacturaRepository:
    TOPIC = settings.KAFKA_TOPICS["factura"]

    def __init__(self, pinot: PinotClient | None = None, kafka: KafkaWriter | None = None):
        self.pinot = pinot or PinotClient()
        self.kafka = kafka or KafkaWriter()

    def _now_ms(self) -> int:
        return int(datetime.now(timezone.utc).timestamp() * 1000)

    def find_by_id(self, id_factura: str) -> dict[str, Any] | None:
        rows = self.pinot.query(
            "SELECT * FROM Fact_Factura WHERE id_factura = %(id)s",
            {"id": id_factura},
        )
        return rows[0] if rows else None

    def list_by_cliente(self, idcliente: int, *, limit: int = 20) -> list[dict[str, Any]]:
        rows = list(self.pinot.query("SELECT * FROM Fact_Factura", {}) or [])
        rows = [r for r in rows if r.get("id_cliente") == idcliente]
        rows.sort(key=lambda r: r.get("fecha_emision") or 0, reverse=True)
        return rows[:limit]

    def find_by_suscripcion_periodo(self, id_suscripcion: int, periodo: str) -> dict[str, Any] | None:
        rows = list(self.pinot.query("SELECT * FROM Fact_Factura", {}) or [])
        for r in rows:
            if r.get("id_suscripcion") == id_suscripcion and r.get("periodo") == periodo:
                return r
        return None

    def _next_seq(self, yyyymm: str) -> int:
        rows = list(self.pinot.query("SELECT * FROM Fact_Factura", {}) or [])
        max_seq = 0
        for r in rows:
            m = _SEQ_RE.match(str(r.get("numero_factura") or ""))
            if m and m.group(1) == yyyymm:
                max_seq = max(max_seq, int(m.group(2)))
        return max_seq + 1

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        now = datetime.now(TZ)
        periodo = data["periodo"]
        yyyymm = periodo.replace("-", "")
        seq = self._next_seq(yyyymm)
        numero = f"FAC-{yyyymm}-{seq:08d}"
        existing = {r.get("numero_factura") for r in (self.pinot.query("SELECT * FROM Fact_Factura", {}) or [])}
        while numero in existing:
            seq += 1
            numero = f"FAC-{yyyymm}-{seq:08d}"
        emision = now
        vencimiento = emision + timedelta(days=7)
        record = {
            "id_factura": str(uuid.uuid4()),
            "id_cliente": data["id_cliente"],
            "id_suscripcion": data["id_suscripcion"],
            "idmetodopago": data.get("idmetodopago"),
            "numero_factura": numero,
            "periodo": periodo,
            "estado_pago": "Pendiente",
            "desglose_cargos": data.get("desglose_cargos", []),
            "monto_base": float(data["monto_base"]),
            "impuestos": 0.0,
            "monto_total": float(data["monto_base"]),
            "fecha_emision": int(emision.timestamp() * 1000),
            "fecha_vencimiento": int(vencimiento.timestamp() * 1000),
            "reintentos": 0,
            "resultado_ultimo_reintento": None,
            "es_nota_credito": False,
            "id_factura_original": None,
            "motivo_anulacion": None,
            "fecha_actualizacion": self._now_ms(),
        }
        self.kafka.publish(self.TOPIC, record)
        return record

    def update(self, id_factura: str, changes: dict[str, Any]) -> dict[str, Any] | None:
        current = self.find_by_id(id_factura)
        if not current:
            return None
        payload = {**current, **changes, "fecha_actualizacion": self._now_ms()}
        self.kafka.publish(self.TOPIC, payload)
        return payload
