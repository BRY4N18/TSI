"""Dim_CredencialAPI repository — credenciales nombradas por entorno (CU-O49).

SEGURIDAD: al topic solo viaja `client_secret_hash`. El secreto en claro NUNCA
sale de la peticion que lo genera — ni a Kafka, ni a logs, ni a esta capa.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from django.conf import settings

from apps.partners.domain_constants import NUNCA_EXPIRA
from core.pinot.client import PinotClient
from core.repositories.partners.kafka_writer import KafkaWriter
from core.pinot.secuencia import siguiente_id


class CredencialRepository:
    TOPIC = settings.KAFKA_TOPICS["credencial_api"]

    def __init__(self, pinot: PinotClient | None = None, kafka: KafkaWriter | None = None):
        self.pinot = pinot or PinotClient()
        self.kafka = kafka or KafkaWriter()

    @staticmethod
    def _now_ms() -> int:
        return int(datetime.now(timezone.utc).timestamp() * 1000)

    def _next_id(self) -> int:
        return siguiente_id(self.pinot, "Dim_CredencialAPI", "idcredencial")

    # --- Lecturas -----------------------------------------------------------

    def find_by_id(self, idcredencial: int) -> dict[str, Any] | None:
        rows = self.pinot.query(
            "SELECT * FROM Dim_CredencialAPI WHERE idcredencial = %(id)s LIMIT 1",
            {"id": idcredencial},
        )
        return rows[0] if rows else None

    def list_by_partner(
        self, idpartner: int, *, entorno: str | None = None, solo_activas: bool = False
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"idpartner": idpartner, "limit": 1000}
        filtros = ["idpartner = %(idpartner)s"]
        if entorno:
            filtros.append("entorno = %(entorno)s")
            params["entorno"] = entorno
        if solo_activas:
            filtros.append("activo = true")
        return self.pinot.query(
            "SELECT * FROM Dim_CredencialAPI WHERE "
            + " AND ".join(filtros)
            + " ORDER BY idcredencial DESC LIMIT %(limit)s",
            params,
        )

    def nombre_en_uso(
        self, idpartner: int, entorno: str, nombre: str, *, excluir: int | None = None
    ) -> bool:
        """RN-PON-014 — el nombre es unico ENTRE LAS ACTIVAS del mismo entorno.

        Un nombre liberado por revocacion o expiracion puede reutilizarse.

        `excluir` permite ignorar una credencial concreta: lo necesita la
        revocacion de #09, que emite el reemplazo con el MISMO nombre y sabe en
        memoria que la anterior acaba de desactivarse — Pinot todavia la veria
        activa y daria una colision falsa.
        """
        for cred in self.list_by_partner(idpartner, entorno=entorno, solo_activas=True):
            if excluir is not None and int(cred["idcredencial"]) == int(excluir):
                continue
            if cred.get("nombre_credencial") == nombre:
                return True
        return False

    def todas_activas(self) -> list[dict[str, Any]]:
        """Todas las credenciales activas del sistema (lo usan los jobs)."""
        return self.pinot.query(
            "SELECT * FROM Dim_CredencialAPI WHERE activo = true LIMIT 10000", {}
        )

    def vencidas(self, ahora_ms: int | None = None) -> list[dict[str, Any]]:
        """Credenciales activas cuya vigencia ya paso (RF-PON-006).

        Las de produccion llevan el centinela `NUNCA_EXPIRA` (ano 9999), asi que
        esta comparacion nunca las alcanza — es justo para eso que el centinela
        esta en el futuro y no en 0.
        """
        return self.pinot.query(
            "SELECT * FROM Dim_CredencialAPI "
            "WHERE activo = true AND fecha_expiracion < %(ahora)s LIMIT 1000",
            {"ahora": ahora_ms if ahora_ms is not None else self._now_ms()},
        )

    # --- Escrituras (via Kafka) ---------------------------------------------

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        """Emite una credencial. `client_secret_hash` YA debe venir hasheado."""
        now = self._now_ms()
        fila = {
            "idcredencial": data.get("idcredencial") or self._next_id(),
            "idpartner": int(data["idpartner"]),
            "idcliente": int(data["idcliente"]),
            "client_secret_hash": data["client_secret_hash"],
            "nombre_credencial": data["nombre_credencial"],
            "entorno": data["entorno"],
            "activo": True,
            "fecha_creacion": now,
            "fecha_expiracion": data.get("fecha_expiracion", NUNCA_EXPIRA),
            "fecha_actualizacion": now,
        }
        self.kafka.publish(self.TOPIC, fila)
        return fila

    def desactivar(self, idcredencial: int) -> dict[str, Any] | None:
        """Marca inactiva. Upsert FULL: se republica la fila completa."""
        actual = self.find_by_id(idcredencial)
        if not actual:
            return None
        fila = {**actual, "activo": False, "fecha_actualizacion": self._now_ms()}
        self.kafka.publish(self.TOPIC, fila)
        return fila

    def activar(self, idcredencial: int) -> dict[str, Any] | None:
        """Restituye una credencial desactivada por cascada (RN-PAC-011).

        **No existe un `activar` de proposito general.** Quien decide QUE se
        restituye es `ReactivarPartnerService`, leyendo las filas de cascada de
        la bitacora: este metodo solo ejecuta. Llamarlo sobre una credencial que
        el partner revoco por seguridad resucitaria una credencial comprometida,
        y por eso la lista de que reactivar no se deriva nunca de esta capa.
        """
        actual = self.find_by_id(idcredencial)
        if not actual:
            return None
        fila = {**actual, "activo": True, "fecha_actualizacion": self._now_ms()}
        self.kafka.publish(self.TOPIC, fila)
        return fila
