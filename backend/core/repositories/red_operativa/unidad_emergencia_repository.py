"""Dim_UnidadEmergencia write repository — CRUD administrativo (CU-O54/56/57/58)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from django.conf import settings

from core.pinot.client import PinotClient
from core.repositories.red_operativa.kafka_writer import KafkaWriter
from core.pinot.secuencia import siguiente_id


class UnidadEmergenciaRepository:
    """Repository for Dim_UnidadEmergencia entity (escritura administrativa)."""

    TOPIC = settings.KAFKA_TOPICS["unidad_emergencia_snapshot"]

    _LIST_COLUMNS = (
        "idunidademergencia",
        "idcliente",
        "idcondado",
        "tipopropiedad",
        "placa",
        "capacidad",
        "contactoproveedor",
        "unidademergencia",
        "tipounidademergencia",
        "idusuario",
        "activo",
        "latitud",
        "longitud",
    )

    def __init__(
        self,
        pinot: PinotClient | None = None,
        kafka: KafkaWriter | None = None,
    ):
        self.pinot = pinot or PinotClient()
        self.kafka = kafka or KafkaWriter()

    def find_by_id(self, idunidademergencia: int) -> dict[str, Any] | None:
        rows = self.pinot.query(
            "SELECT * FROM Dim_UnidadEmergencia WHERE idunidademergencia = %(idunidademergencia)s LIMIT 1",
            {"idunidademergencia": idunidademergencia},
        )
        return self._normalize_row(rows[0]) if rows else None

    def find_by_placa_activa(self, placa: str) -> dict[str, Any] | None:
        rows = self.pinot.query(
            "SELECT * FROM Dim_UnidadEmergencia WHERE placa = %(placa)s AND activo = true LIMIT 1",
            {"placa": placa},
        )
        return self._normalize_row(rows[0]) if rows else None

    def find_by_placa(self, placa: str) -> dict[str, Any] | None:
        """Busca la placa **en cualquier estado**, también entre las dadas de baja.

        La placa es el identificador único de negocio y una unidad de baja conserva
        la suya —el SRS §3.5.1 permite reactivarla—. Comprobar solo entre las activas
        dejaba registrar una unidad nueva con la placa de una de baja, y al reactivar
        la antigua quedaban dos unidades activas con la misma placa.
        """
        rows = self.pinot.query(
            "SELECT * FROM Dim_UnidadEmergencia WHERE placa = %(placa)s "
            "ORDER BY idunidademergencia DESC LIMIT 1",
            {"placa": placa},
        )
        return self._normalize_row(rows[0]) if rows else None

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        now = self._now_ms()
        idunidademergencia = self._next_id()
        payload = {
            "idunidademergencia": int(idunidademergencia),
            "idcliente": int(data["idcliente"]),
            "idcondado": int(data["idcondado"]),
            "tipopropiedad": data["tipopropiedad"],
            "placa": data["placa"],
            "capacidad": data.get("capacidad"),
            "contactoproveedor": data.get("contactoproveedor"),
            "unidademergencia": data["unidademergencia"],
            "tipounidademergencia": data["tipounidademergencia"],
            "idusuario": self._optional_int(data.get("idusuario")),
            "activo": bool(data.get("activo", True)),
            "latitud": data.get("latitud"),
            "longitud": data.get("longitud"),
            "fecha_actualizacion": now,
        }
        self.kafka.publish(self.TOPIC, payload)
        return payload

    def list_by_cliente(
        self,
        idcliente: int,
        *,
        cursor: int = 0,
        limit: int = 20,
        q: str | None = None,
        activo: bool | None = None,
        tipounidademergencia: str | None = None,
        solo_activas: bool = False,
    ) -> tuple[list[dict[str, Any]], int | None]:
        """Página de flota del cliente. Orden ASC por id; next_cursor o None."""
        # Pinot broker default LIMIT is 10 — raise for full-fleet filter/page in Python.
        rows = self.pinot.query(
            "SELECT * FROM Dim_UnidadEmergencia WHERE idcliente = %(idcliente)s LIMIT 10000",
            {"idcliente": int(idcliente)},
        )
        if solo_activas and activo is None:
            activo = True

        cursor_i = max(0, int(cursor or 0))
        limit_i = max(1, min(int(limit or 20), 100))
        q_norm = (q or "").strip().lower()
        tipo_norm = (tipounidademergencia or "").strip() or None

        filtered: list[dict[str, Any]] = []
        for row in rows:
            normalized = self._normalize_row(row) or {}
            uid = int(normalized.get("idunidademergencia") or 0)
            if uid <= cursor_i:
                continue
            if activo is not None and bool(normalized.get("activo")) is not bool(activo):
                continue
            if tipo_norm and str(normalized.get("tipounidademergencia") or "") != tipo_norm:
                continue
            if q_norm:
                placa = str(normalized.get("placa") or "").lower()
                nombre = str(normalized.get("unidademergencia") or "").lower()
                if q_norm not in placa and q_norm not in nombre:
                    continue
            filtered.append({k: normalized.get(k) for k in self._LIST_COLUMNS})

        filtered.sort(key=lambda r: int(r["idunidademergencia"]))
        page = filtered[:limit_i]
        next_cursor: int | None = None
        if len(filtered) > limit_i:
            next_cursor = int(page[-1]["idunidademergencia"])
        return page, next_cursor

    def update(
        self,
        idunidademergencia: int,
        data: dict[str, Any],
        *,
        base: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        existing = self._normalize_row(base) if base is not None else self.find_by_id(idunidademergencia)
        if not existing:
            return None
        now = self._now_ms()
        merged = {**existing, **data}
        idcondado = merged.get("idcondado")
        if idcondado is None:
            raise ValueError("idcondado es requerido para actualizar la unidad")
        payload = {
            "idunidademergencia": int(idunidademergencia),
            "idcliente": int(merged["idcliente"]),
            "idcondado": int(idcondado),
            "tipopropiedad": merged.get("tipopropiedad"),
            "placa": merged.get("placa"),
            "capacidad": merged.get("capacidad"),
            "contactoproveedor": merged.get("contactoproveedor"),
            "unidademergencia": merged.get("unidademergencia"),
            "tipounidademergencia": merged.get("tipounidademergencia"),
            "idusuario": self._optional_int(merged.get("idusuario")),
            "activo": bool(merged.get("activo", True)),
            "latitud": merged.get("latitud"),
            "longitud": merged.get("longitud"),
            "fecha_creacion": merged.get("fecha_creacion"),
            "fecha_actualizacion": now,
        }
        self.kafka.publish(self.TOPIC, payload)
        return payload

    def _next_id(self) -> int:
        return siguiente_id(self.pinot, "Dim_UnidadEmergencia", "idunidademergencia")

    def condado_exists(self, idcondado: int) -> bool:
        rows = self.pinot.query(
            "SELECT idcondado FROM Dim_Condado WHERE idcondado = %(idcondado)s LIMIT 1",
            {"idcondado": idcondado},
        )
        return bool(rows)

    # Pinot INT null sentinel when enableColumnBasedNullHandling is false.
    _INT_NULL = -2147483648

    @classmethod
    def _coerce_idcondado(cls, value: Any) -> int | None:
        if value is None or value == "" or value == "null":
            return None
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return None
        if parsed == cls._INT_NULL:
            return None
        return parsed

    @classmethod
    def _normalize_row(cls, row: dict[str, Any] | None) -> dict[str, Any] | None:
        """Ensure idcondado INT; map legacy zonacobertura when needed."""
        if not row:
            return None
        out = dict(row)
        idcondado = cls._coerce_idcondado(out.get("idcondado"))
        if idcondado is None:
            idcondado = cls._coerce_idcondado(out.get("zonacobertura"))
        if idcondado is not None:
            out["idcondado"] = idcondado
        else:
            out.pop("idcondado", None)
        out.pop("zonacobertura", None)
        return out

    @staticmethod
    def _now_ms() -> int:
        return int(datetime.now(timezone.utc).timestamp() * 1000)

    @staticmethod
    def _optional_int(value: Any) -> int | None:
        if value is None or value == "":
            return None
        return int(value)
