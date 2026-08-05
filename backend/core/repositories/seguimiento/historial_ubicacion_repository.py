"""Dim_HistorialUbicacionUnidadEmergencia — Pinot read, Kafka write."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from django.conf import settings

from core.pinot.client import PinotClient
from core.repositories.accidentes.kafka_writer import KafkaWriter


class HistorialUbicacionRepository:
    TOPIC = settings.KAFKA_TOPICS["historial_ubicacion_unidad"]

    def __init__(self, pinot: PinotClient | None = None, kafka: KafkaWriter | None = None):
        self.pinot = pinot or PinotClient()
        self.kafka = kafka or KafkaWriter()

    def _next_id(self) -> int:
        rows = self.pinot.query(
            """
            SELECT MAX(idhistorialunidademergencia) AS max_id
            FROM Dim_HistorialUbicacionUnidadEmergencia
            """,
            {},
        )
        return int(rows[0]["max_id"] or 0) + 1 if rows else 1

    def publish(
        self,
        *,
        idunidademergencia: int,
        idaccidente: str,
        latitud: float,
        longitud: float,
        fechahora: int | None = None,
    ) -> dict[str, Any]:
        now = fechahora or int(datetime.now(timezone.utc).timestamp() * 1000)
        payload = {
            "idhistorialunidademergencia": self._next_id(),
            "idunidademergencia": idunidademergencia,
            "idaccidente": idaccidente,
            "latitud": latitud,
            "longitud": longitud,
            "fechahora": now,
            "fecha_actualizacion": now,
        }
        self.kafka.publish(self.TOPIC, payload)
        return payload

    # Tamaño de bloque al recorrer la traza GPS. Es la tabla que más rápido crece
    # del sistema: cada unidad en misión publica una posición cada ~10 s, así que
    # una jornada de 8 h por unidad son ~2.900 filas.
    BLOQUE_LECTURA = 500
    MAX_BLOQUES = 200

    def list_by_unidad(
        self,
        idunidademergencia: int,
        *,
        desde: int | None = None,
        hasta: int | None = None,
        limit: int = BLOQUE_LECTURA,
        cursor: int | None = None,
    ) -> tuple[list[dict[str, Any]], int | None]:
        """Una página de la traza GPS de la unidad, resuelta en Pinot.

        Ventana temporal, orden y tope viajan en el SQL. La paginación es keyset
        sobre `idhistorialunidademergencia`, que es monótono porque se asigna con
        MAX(id)+1 en cada publicación.

        Devuelve (filas, cursor_siguiente); cursor_siguiente es None en la última
        página.
        """
        condiciones = ["idunidademergencia = %(idunidademergencia)s"]
        params: dict[str, Any] = {
            "idunidademergencia": idunidademergencia,
            "limit": limit + 1,
        }
        if desde is not None:
            condiciones.append("fechahora >= %(desde)s")
            params["desde"] = desde
        if hasta is not None:
            condiciones.append("fechahora <= %(hasta)s")
            params["hasta"] = hasta
        if cursor is not None:
            condiciones.append("idhistorialunidademergencia > %(cursor)s")
            params["cursor"] = cursor

        rows = self.pinot.query(
            f"""
            SELECT * FROM Dim_HistorialUbicacionUnidadEmergencia
            WHERE {' AND '.join(condiciones)}
            ORDER BY idhistorialunidademergencia
            LIMIT %(limit)s
            """,
            params,
        )
        pagina = rows[:limit]
        siguiente = (
            int(pagina[-1]["idhistorialunidademergencia"]) if len(rows) > limit and pagina else None
        )
        return pagina, siguiente

    def iter_by_unidad(
        self,
        idunidademergencia: int,
        *,
        desde: int | None = None,
        hasta: int | None = None,
    ):
        """Recorre toda la traza de la unidad por bloques, sin cargarla entera.

        Para los consumidores que sí necesitan ver todos los puntos (job de
        depuración GPS, exportación de expediente). Cada bloque es una consulta
        acotada; el siguiente arranca donde terminó el anterior.
        """
        cursor: int | None = None
        for _ in range(self.MAX_BLOQUES):
            bloque, siguiente = self.list_by_unidad(
                idunidademergencia,
                desde=desde,
                hasta=hasta,
                limit=self.BLOQUE_LECTURA,
                cursor=cursor,
            )
            yield from bloque
            if siguiente is None:
                return
            cursor = siguiente

    def latest_fechahora(self, idunidademergencia: int) -> int | None:
        rows = self.pinot.query(
            """
            SELECT fechahora FROM Dim_HistorialUbicacionUnidadEmergencia
            WHERE idunidademergencia = %(idunidademergencia)s
            ORDER BY fechahora DESC
            LIMIT 1
            """,
            {"idunidademergencia": idunidademergencia},
        )
        if not rows:
            return None
        return int(rows[0]["fechahora"])
