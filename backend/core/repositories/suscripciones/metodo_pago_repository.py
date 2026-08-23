"""Dim_MetodoPago repository — RF-SUSF-002."""

from __future__ import annotations

from typing import Any

from django.conf import settings

from core.pinot.client import PinotClient
from core.pinot.tiempo import SIN_FECHA, ahora_ms, mes_anio_a_ms
from core.repositories.suscripciones.kafka_writer import KafkaWriter
from core.pinot.secuencia import siguiente_id


class MetodoPagoRepository:
    TOPIC = settings.KAFKA_TOPICS["metodo_pago"]

    def __init__(self, pinot: PinotClient | None = None, kafka: KafkaWriter | None = None):
        self.pinot = pinot or PinotClient()
        self.kafka = kafka or KafkaWriter()

    def _now_ms(self) -> int:
        return ahora_ms()

    @staticmethod
    def _expiracion_ms(valor: Any) -> int:
        """`fechaexpiracion` es LONG epoch-millis: nunca publicar el texto `MM/AA`.

        Al releer una fila para republicarla, Pinot puede devolver el epoch ya
        convertido a cadena; eso no se vuelve a interpretar como `MM/AA`.
        """
        if isinstance(valor, int):
            return valor
        texto = str(valor).strip() if valor is not None else ""
        if texto.lstrip("-").isdigit():
            return int(texto)
        return mes_anio_a_ms(texto)

    def _next_id(self) -> int:
        return siguiente_id(self.pinot, "Dim_MetodoPago", "idmetodopago")

    def find_by_id(self, idmetodopago: int) -> dict[str, Any] | None:
        rows = self.pinot.query(
            "SELECT * FROM Dim_MetodoPago WHERE idmetodopago = %(id)s",
            {"id": idmetodopago},
        )
        return rows[0] if rows else None

    def list_by_cliente(self, idcliente: int) -> list[dict[str, Any]]:
        # El filtro va en SQL y el LIMIT es explícito: sin él Pinot aplica un
        # `LIMIT 10` implícito sobre la tabla entera, así que los métodos de un
        # cliente podían no aparecer nunca por culpa de los de otros clientes.
        rows = self.pinot.query(
            "SELECT * FROM Dim_MetodoPago WHERE idcliente = %(idcliente)s "
            "ORDER BY idmetodopago DESC LIMIT 1000",
            {"idcliente": idcliente},
        )
        return list(rows or [])

    def find_activo(self, idcliente: int) -> dict[str, Any] | None:
        for row in self.list_by_cliente(idcliente):
            if row.get("activo"):
                return row
        return None

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        record = {
            "idmetodopago": self._next_id(),
            "idcliente": data["idcliente"],
            "tipo": data["tipo"],
            "tokenpasarela": data["tokenpasarela"],
            "ultimosdigitos": data.get("ultimosdigitos", "")[:4],
            "fechaexpiracion": self._expiracion_ms(data.get("fechaexpiracion")),
            "activo": True,
            "fecha_actualizacion": self._now_ms(),
        }
        self.kafka.publish(self.TOPIC, record)
        return record

    def update(self, idmetodopago: int, changes: dict[str, Any]) -> dict[str, Any] | None:
        current = self.find_by_id(idmetodopago)
        if not current:
            return None
        payload = {**current, **changes, "fecha_actualizacion": self._now_ms()}
        payload["fechaexpiracion"] = self._expiracion_ms(payload.get("fechaexpiracion"))
        self.kafka.publish(self.TOPIC, payload)
        return payload
