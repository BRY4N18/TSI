"""Dim_NotaAccidente repository for field notes (CU-O27)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from django.conf import settings

from core.pinot.client import PinotClient
from core.repositories.accidentes.kafka_writer import KafkaWriter

TIPOS_NOTA_CAMPO = frozenset(
    {
        "Observación general",
        "Declaración de testigo",
        "Daños materiales",
        "Condiciones del sitio",
    }
)


class NotaCampoRepository:
    TOPIC = settings.KAFKA_TOPICS["nota_accidente"]

    def __init__(self, pinot: PinotClient | None = None, kafka: KafkaWriter | None = None):
        self.pinot = pinot or PinotClient()
        self.kafka = kafka or KafkaWriter()

    def _next_id(self) -> int:
        rows = self.pinot.query(
            "SELECT MAX(idnotaaccidentes) AS max_id FROM Dim_NotaAccidente",
            {},
        )
        return int(rows[0]["max_id"] or 0) + 1 if rows else 1

    def list_by_accidente(
        self,
        idaccidente: str,
        *,
        tipo: str | None = None,
        limit: int = 20,
        cursor: int | None = None,
    ) -> list[dict[str, Any]]:
        rows = self.pinot.query(
            """
            SELECT * FROM Dim_NotaAccidente
            WHERE idaccidente = %(idaccidente)s
            """,
            {"idaccidente": idaccidente},
        )
        rows = [
            r
            for r in rows
            if r.get("sincronizado") is True and r.get("tipo") in TIPOS_NOTA_CAMPO
        ]
        if tipo:
            rows = [r for r in rows if r.get("tipo") == tipo]
        rows.sort(key=lambda r: r.get("fechahora", 0), reverse=True)
        if cursor is not None:
            rows = [r for r in rows if r.get("idnotaaccidentes", 0) < cursor]
        return rows[:limit]

    def create_campo(
        self,
        *,
        idaccidente: str,
        idusuario: int,
        nota: str,
        tipo: str,
        fechahora: int,
    ) -> dict[str, Any]:
        if tipo not in TIPOS_NOTA_CAMPO:
            raise ValueError(f"Tipo de nota inválido: {tipo}")
        now = int(datetime.now(timezone.utc).timestamp() * 1000)
        payload = {
            "idnotaaccidentes": self._next_id(),
            "idaccidente": idaccidente,
            "idusuario": idusuario,
            "nota": nota,
            "tipo": tipo,
            "sincronizado": True,
            "fechahora": fechahora,
            "fecha_actualizacion": now,
            "activo": True,
        }
        self.kafka.publish(self.TOPIC, payload)
        return payload
