"""Fact_Accidente repository — Pinot read, Kafka write."""

from __future__ import annotations

import random
import time
from datetime import datetime, timezone
from typing import Any

from django.conf import settings

from core.pinot.client import PinotClient
from core.repositories.accidentes.kafka_writer import KafkaWriter
from core.repositories.accidentes.ubicacion_catalogo_repository import (
    UbicacionCatalogoRepository,
)


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

    def calles_de_ubicacion(
        self, idciudad: int | None, idestadoregion: int | None
    ) -> set[int] | None:
        """Calles que caen dentro del filtro geográfico, o None si no hay filtro.

        Un conjunto vacío significa "el filtro es válido pero no cubre ninguna
        calle", que no es lo mismo que "sin filtro": el llamador debe devolver
        cero resultados en vez de listar todo.
        """
        if idciudad is None and idestadoregion is None:
            return None
        calles: set[int] = set()
        if idciudad is not None:
            calles.update(c["id"] for c in self.catalogo_repo.listar_calles(idciudad))
        if idestadoregion is not None:
            for condado in self.catalogo_repo.listar_condados(idestadoregion):
                for ciudad in self.catalogo_repo.listar_ciudades(condado["id"]):
                    calles.update(c["id"] for c in self.catalogo_repo.listar_calles(ciudad["id"]))
        return calles

    def list_activos(
        self,
        *,
        idseveridad: int | None = None,
        activo: bool | None = True,
        fecha_desde: int | None = None,
        fecha_hasta: int | None = None,
        idciudad: int | None = None,
        idestadoregion: int | None = None,
        limit: int = 20,
        cursor: str | None = None,
    ) -> tuple[list[dict[str, Any]], str | None]:
        """Una página de accidentes, resuelta enteramente en Pinot.

        Filtros, orden y tope viajan en el SQL: se traen `limit + 1` filas para
        saber si hay página siguiente y nada más. No se materializa la tabla en
        memoria del servidor — avanzar de página emite una consulta nueva
        acotada por el cursor (paginación keyset sobre `idaccidente`, que es
        monótono en el tiempo por construcción: ACC-{epoch_ms}-{aleatorio}).

        `activo=None` deja el campo fuera del filtro: lo necesita el historial,
        porque cerrar un caso lo marca `activo=False` y aun así debe listarse.

        Devuelve (filas, cursor_siguiente); cursor_siguiente es None en la
        última página.
        """
        calles = self.calles_de_ubicacion(idciudad, idestadoregion)
        if calles is not None and not calles:
            return [], None

        condiciones: list[str] = []
        params: dict[str, Any] = {"limit": limit + 1}
        if activo is not None:
            condiciones.append("activo = %(activo)s")
            params["activo"] = activo
        if idseveridad is not None:
            condiciones.append("idseveridad = %(idseveridad)s")
            params["idseveridad"] = idseveridad
        if fecha_desde is not None:
            condiciones.append("fechahoraaccidente >= %(fecha_desde)s")
            params["fecha_desde"] = fecha_desde
        if fecha_hasta is not None:
            condiciones.append("fechahoraaccidente <= %(fecha_hasta)s")
            params["fecha_hasta"] = fecha_hasta
        if calles is not None:
            condiciones.append("idcalle IN %(idscalle)s")
            params["idscalle"] = sorted(calles)
        if cursor:
            condiciones.append("idaccidente < %(cursor)s")
            params["cursor"] = cursor

        where = f"WHERE {' AND '.join(condiciones)}" if condiciones else ""
        rows = self.pinot.query(
            f"""
            SELECT * FROM Fact_Accidente
            {where}
            ORDER BY idaccidente DESC
            LIMIT %(limit)s
            """,
            params,
        )
        pagina = rows[:limit]
        siguiente = pagina[-1]["idaccidente"] if len(rows) > limit and pagina else None
        return pagina, siguiente

    def find_nearby(
        self,
        *,
        latitud: float,
        longitud: float,
        fechahoraaccidente: int,
        window_ms: int,
        exclude_id: str | None = None,
    ) -> list[dict[str, Any]]:
        # Único caso que no pagina: agrupar reportes duplicados exige mirar todo
        # el conjunto candidato de una vez, porque un duplicado que quedara fuera
        # de la página se registraría como accidente nuevo. La ventana temporal
        # va en el SQL para que el escaneo no crezca con la historia completa.
        rows = self.pinot.query(
            """
            SELECT * FROM Fact_Accidente
            WHERE activo = true
              AND fechahoraaccidente >= %(desde)s
              AND fechahoraaccidente <= %(hasta)s
            """,
            {
                "desde": fechahoraaccidente - window_ms,
                "hasta": fechahoraaccidente + window_ms,
            },
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
