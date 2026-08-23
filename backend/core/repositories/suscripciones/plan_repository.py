"""Dim_Plan repository — catálogo de planes (RF-SUSF-001)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from django.conf import settings

from core.pinot.client import PinotClient
from core.repositories.suscripciones.kafka_writer import KafkaWriter
from core.pinot.secuencia import siguiente_id


class PlanRepository:
    TOPIC = settings.KAFKA_TOPICS["plan"]

    def __init__(self, pinot: PinotClient | None = None, kafka: KafkaWriter | None = None):
        self.pinot = pinot or PinotClient()
        self.kafka = kafka or KafkaWriter()

    def _now_ms(self) -> int:
        return int(datetime.now(timezone.utc).timestamp() * 1000)

    def _next_id(self) -> int:
        return siguiente_id(self.pinot, "Dim_Plan", "idplan")

    def find_by_id(self, idplan: int) -> dict[str, Any] | None:
        rows = self.pinot.query(
            "SELECT * FROM Dim_Plan WHERE idplan = %(idplan)s LIMIT 1",
            {"idplan": idplan},
        )
        return rows[0] if rows else None

    def list(
        self,
        *,
        cursor: int | None = None,
        limit: int = 20,
        q: str | None = None,
        activo: bool | None = None,
        nivel: str | None = None,
        solo_activos: bool | None = None,
    ) -> tuple[list[dict[str, Any]], int | None]:
        """Página de Dim_Plan ordenada por idplan ASC (Decision 13 / RNF-SUSF-005a).

        Prohibido: SELECT * sin tope + filtrar el universo en Python.
        """
        if solo_activos is True and activo is None:
            activo = True
        elif solo_activos is False and activo is None:
            activo = None

        limit_i = max(1, min(int(limit or 20), 100))
        cursor_i = max(0, int(cursor or 0))
        fetch = limit_i + 1

        clauses = ["idplan > %(cursor)s"]
        params: dict[str, Any] = {"cursor": cursor_i, "limit": fetch}

        if activo is not None:
            clauses.append("activo = %(activo)s")
            params["activo"] = bool(activo)
        if nivel:
            clauses.append("nivel = %(nivel)s")
            params["nivel"] = str(nivel)
        q_norm = (q or "").strip()
        if q_norm:
            clauses.append("LOWER(nombre) LIKE %(q)s")
            params["q"] = f"%{q_norm.lower()}%"

        where = " AND ".join(clauses)
        sql = (
            "SELECT idplan, nombre, precio, limites, nivel, periodicidad, "
            "severidades_desbloqueadas, carga_lote_habilitada, activo, fecha_actualizacion "
            f"FROM Dim_Plan WHERE {where} ORDER BY idplan ASC LIMIT %(limit)s"
        )
        rows = list(self.pinot.query(sql, params) or [])
        next_cursor: int | None = None
        if len(rows) > limit_i:
            page = rows[:limit_i]
            next_cursor = int(page[-1]["idplan"])
        else:
            page = rows
        return page, next_cursor

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        limites = data.get("limites", {})
        if isinstance(limites, dict):
            limites = json.dumps(limites, ensure_ascii=False)
        severidades = data.get("severidades_desbloqueadas", [])
        if isinstance(severidades, list):
            severidades = json.dumps(severidades, ensure_ascii=False)
        record = {
            "idplan": self._next_id(),
            "nombre": data["nombre"],
            "precio": float(data["precio"]),
            "limites": limites,
            "nivel": data["nivel"],
            "periodicidad": data.get("periodicidad") or "Mensual",
            "severidades_desbloqueadas": severidades,
            "carga_lote_habilitada": bool(data.get("carga_lote_habilitada", False)),
            "activo": True,
            "fecha_actualizacion": self._now_ms(),
        }
        self.kafka.publish(self.TOPIC, record)
        return record

    def update(self, idplan: int, changes: dict[str, Any]) -> dict[str, Any] | None:
        current = self.find_by_id(idplan)
        if not current:
            return None
        payload = {**current, **changes, "fecha_actualizacion": self._now_ms()}
        if isinstance(payload.get("limites"), dict):
            payload["limites"] = json.dumps(payload["limites"], ensure_ascii=False)
        if isinstance(payload.get("severidades_desbloqueadas"), list):
            payload["severidades_desbloqueadas"] = json.dumps(
                payload["severidades_desbloqueadas"], ensure_ascii=False
            )
        self.kafka.publish(self.TOPIC, payload)
        return payload
