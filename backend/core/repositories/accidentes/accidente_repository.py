"""Fact_Accidente repository — Pinot read, Kafka write."""

from __future__ import annotations

import time
import random
from datetime import datetime, timezone
from typing import Any

from django.conf import settings

from core.pinot.client import PinotClient
from core.repositories.accidentes.kafka_writer import KafkaWriter
from core.repositories.accidentes.ubicacion_catalogo_repository import UbicacionCatalogoRepository


class AccidenteRepository:
    TOPIC = settings.KAFKA_TOPICS["accidente"]

    def __init__(
        self,
        pinot: PinotClient | None = None,
        kafka: KafkaWriter | None = None,
        catalogo_repo: UbicacionCatalogoRepository | None = None,
    ):
        self.pinot = pinot or PinotClient()
        self.kafka = kafka or KafkaWriter()
        self.catalogo_repo = catalogo_repo or UbicacionCatalogoRepository(self.pinot)

    def find_by_id(self, idaccidente: str) -> dict[str, Any] | None:
        rows = self.pinot.query(
            "SELECT * FROM Fact_Accidente WHERE idaccidente = %(idaccidente)s LIMIT 1",
            {"idaccidente": idaccidente},
        )
        return rows[0] if rows else None

    def list_activos(
        self,
        *,
        idseveridad: int | None = None,
        activo: bool = True,
        fecha_desde: int | None = None,
        fecha_hasta: int | None = None,
        idciudad: int | None = None,
        idestadoregion: int | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        rows = self.pinot.query(
            """
            SELECT * FROM Fact_Accidente
            WHERE activo = %(activo)s
            """,
            {"activo": activo},
        )
        if idseveridad is not None:
            rows = [r for r in rows if r.get("idseveridad") == idseveridad]
        if fecha_desde is not None:
            rows = [r for r in rows if r.get("fechahoraaccidente", 0) >= fecha_desde]
        if fecha_hasta is not None:
            rows = [r for r in rows if r.get("fechahoraaccidente", 0) <= fecha_hasta]
        if idciudad is not None:
            calles = {c["id"] for c in self.catalogo_repo.listar_calles(idciudad)}
            rows = [r for r in rows if r.get("idcalle") in calles]
        if idestadoregion is not None:
            condados = self.catalogo_repo.listar_condados(idestadoregion)
            ciudades: set[int] = set()
            for condado in condados:
                ciudades.update(c["id"] for c in self.catalogo_repo.listar_ciudades(condado["id"]))
            calles: set[int] = set()
            for idciudad_estado in ciudades:
                calles.update(c["id"] for c in self.catalogo_repo.listar_calles(idciudad_estado))
            rows = [r for r in rows if r.get("idcalle") in calles]
        return rows[:limit]

    def find_nearby(
        self,
        *,
        latitud: float,
        longitud: float,
        fechahoraaccidente: int,
        window_ms: int,
        exclude_id: str | None = None,
    ) -> list[dict[str, Any]]:
        rows = self.pinot.query(
            """
            SELECT * FROM Fact_Accidente
            WHERE activo = true
            """,
            {},
        )
        results = []
        for row in rows:
            if exclude_id and row.get("idaccidente") == exclude_id:
                continue
            ts = row.get("fechahoraaccidente", 0)
            if abs(ts - fechahoraaccidente) > window_ms:
                continue
            lat_diff = abs(row.get("latitudinicio", 0) - latitud)
            lon_diff = abs(row.get("longitudinicio", 0) - longitud)
            if lat_diff < 0.0005 and lon_diff < 0.0005:
                results.append(row)
        return results

    def generate_id(self) -> str:
        epoch_ms = int(time.time() * 1000)
        suffix = random.randint(1000, 9999)
        return f"ACC-{epoch_ms}-{suffix}"

    def create(self, payload: dict[str, Any]) -> dict[str, Any]:
        now = int(datetime.now(timezone.utc).timestamp() * 1000)
        record = {
            **payload,
            "fecha_actualizacion": now,
            "activo": payload.get("activo", True),
        }
        self.kafka.publish(self.TOPIC, record)
        return record

    def update(self, idaccidente: str, fields: dict[str, Any]) -> dict[str, Any] | None:
        current = self.find_by_id(idaccidente)
        if not current:
            return None
        now = int(datetime.now(timezone.utc).timestamp() * 1000)
        updated = {**current, **fields, "fecha_actualizacion": now}
        self.kafka.publish(self.TOPIC, updated)
        return updated
