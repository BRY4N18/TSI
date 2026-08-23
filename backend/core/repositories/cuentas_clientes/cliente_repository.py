"""Cliente repository — Dim_Cliente read via Pinot, write via Kafka."""

from __future__ import annotations

from typing import Any

from django.conf import settings

from core.pinot.client import PinotClient
from core.pinot.tiempo import ahora_ms
from core.repositories.cuentas_clientes.kafka_writer import KafkaWriter
from core.pinot.secuencia import siguiente_id

# Valores canónicos de `Dim_Cliente.estado`. Estaban repartidos como literales
# entre `aprobacion_proveedor_service`, `baja_cuenta_service` y este módulo; se
# nombran aquí por la misma razón que en `credential_repository` y en
# `session_repository`: el informe táctico de cuentas por estado filtra por
# ellos, y un literal copiado con una divergencia de un carácter devolvería un
# listado vacío con `200`, sin error y sin nada que lo distinga de "no hay
# cuentas en ese estado".
ESTADO_CLIENTE_ACTIVO = "Activo"
ESTADO_CLIENTE_PENDIENTE = "Pendiente"
ESTADO_CLIENTE_RECHAZADO = "Rechazado"
ESTADO_CLIENTE_RECHAZADO_ANULADO = "Rechazado_Anulado"
ESTADO_CLIENTE_BAJA = "Dado de baja"

ESTADOS_CLIENTE = frozenset(
    {
        ESTADO_CLIENTE_ACTIVO,
        ESTADO_CLIENTE_PENDIENTE,
        ESTADO_CLIENTE_RECHAZADO,
        ESTADO_CLIENTE_RECHAZADO_ANULADO,
        ESTADO_CLIENTE_BAJA,
    }
)


class ClienteRepository:
    """Repository for Dim_Cliente entity."""

    TOPIC = settings.KAFKA_TOPICS["cliente"]

    def __init__(
        self,
        pinot: PinotClient | None = None,
        kafka: KafkaWriter | None = None,
    ):
        self.pinot = pinot or PinotClient()
        self.kafka = kafka or KafkaWriter()

    def find_by_id(self, cliente_id: int) -> dict[str, Any] | None:
        rows = self.pinot.query(
            "SELECT * FROM Dim_Cliente WHERE idcliente = %(idcliente)s LIMIT 1",
            {"idcliente": cliente_id},
        )
        return rows[0] if rows else None

    def find_by_nit(self, nit: str) -> dict[str, Any] | None:
        """NIT activo para duplicados — excluye soft-anulados (Rechazado_Anulado)."""
        rows = self.pinot.query(
            """
            SELECT * FROM Dim_Cliente
            WHERE nit_identificacion = %(nit)s
              AND estado <> 'Rechazado_Anulado'
            LIMIT 1
            """,
            {"nit": nit},
        )
        return rows[0] if rows else None

    def exists_by_nit_any(self, nit: str) -> bool:
        """Return whether a NIT exists regardless of the client's state."""
        rows = self.pinot.query(
            "SELECT idcliente FROM Dim_Cliente WHERE nit_identificacion = %(nit)s LIMIT 1",
            {"nit": nit},
        )
        return bool(rows)

    def find_by_admin_local(self, user_id: int) -> dict[str, Any] | None:
        """Cuenta vigente del admin local — excluye soft-anulados."""
        rows = self.pinot.query(
            """
            SELECT * FROM Dim_Cliente
            WHERE admin_local_id = %(admin_local_id)s
              AND estado <> 'Rechazado_Anulado'
            LIMIT 1
            """,
            {"admin_local_id": user_id},
        )
        return rows[0] if rows else None

    def list_by_estado(self, estado: str) -> list[dict[str, Any]]:
        rows = self.pinot.query(
            """
            SELECT * FROM Dim_Cliente
            WHERE estado = %(estado)s
            """,
            {"estado": estado},
        )
        return list(rows or [])

    def update_estado(
        self,
        cliente_id: int,
        *,
        estado: str,
        estado_onboarding: str | None = None,
        fecha_inicio_contrato: int | None = None,
    ) -> dict[str, Any] | None:
        """Cambia el estado de la cuenta y, si se indica, sella el inicio del contrato.

        ⚠️ `fecha_inicio_contrato` **solo se escribe cuando llega**, y nunca se
        pisa un valor previo con `None`: `update` fusiona sobre la fila
        existente, así que omitir la clave conserva lo que hubiera. Una
        reactivación no debe reescribir la fecha del contrato original.
        """
        data: dict[str, Any] = {"estado": estado}
        if estado_onboarding is not None:
            data["estado_onboarding"] = estado_onboarding
        if fecha_inicio_contrato is not None:
            data["fecha_inicio_contrato"] = fecha_inicio_contrato
        return self.update(cliente_id, data)

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        now = ahora_ms()
        cliente_id = self._next_id()
        payload = {
            "idcliente": cliente_id,
            "razon_social": data["razon_social"],
            "nombre": data.get("nombre", ""),
            "tipo": data["tipo"],
            "nit_identificacion": data["nit_identificacion"],
            "fecha_inicio_contrato": data.get("fecha_inicio_contrato"),
            "plan_suscripcion": data.get("plan_suscripcion"),
            "logo_url": data.get("logo_url"),
            "estado_onboarding": data.get("estado_onboarding"),
            "estado": data.get("estado", "Activo"),
            "idprospecto": data.get("idprospecto"),
            "admin_local_id": data.get("admin_local_id"),
            "fecha_actualizacion": now,
        }
        self.kafka.publish(self.TOPIC, payload)
        return payload

    def update(self, cliente_id: int, data: dict[str, Any]) -> dict[str, Any] | None:
        existing = self.find_by_id(cliente_id)
        if not existing:
            return None
        now = ahora_ms()
        payload = {**existing, **data, "fecha_actualizacion": now}
        self.kafka.publish(self.TOPIC, payload)
        return payload

    def _next_id(self) -> int:
        return siguiente_id(self.pinot, "Dim_Cliente", "idcliente")
