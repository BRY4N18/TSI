"""Posición efectiva de unidad — RN-DES-010."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from core.pinot.client import PinotClient


def _to_epoch_ms(value: Any) -> int:
    if value is None:
        return 0
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            normalized = value.replace("Z", "+00:00")
            return int(datetime.fromisoformat(normalized).timestamp() * 1000)
    return 0


class UbicacionUnidadRepository:
    def __init__(self, pinot: PinotClient | None = None):
        self.pinot = pinot or PinotClient()

    def _latest_gps(self, idunidademergencia: int) -> dict[str, Any] | None:
        rows = self.pinot.query(
            """
            SELECT latitud, longitud, fechahora
            FROM Dim_HistorialUbicacionUnidadEmergencia
            WHERE idunidademergencia = %(idunidademergencia)s
            ORDER BY fechahora DESC
            LIMIT 1
            """,
            {"idunidademergencia": idunidademergencia},
        )
        return rows[0] if rows else None

    def posicion_efectiva(self, idunidademergencia: int) -> dict[str, float] | None:
        unit_rows = self.pinot.query(
            """
            SELECT latitud, longitud, fecha_actualizacion
            FROM Dim_UnidadEmergencia
            WHERE idunidademergencia = %(idunidademergencia)s
            LIMIT 1
            """,
            {"idunidademergencia": idunidademergencia},
        )
        if not unit_rows:
            return None
        unit = unit_rows[0]
        snapshot_ts = _to_epoch_ms(unit.get("fecha_actualizacion"))
        gps = self._latest_gps(idunidademergencia)
        if gps and _to_epoch_ms(gps.get("fechahora")) > snapshot_ts:
            return {
                "latitud": float(gps["latitud"]),
                "longitud": float(gps["longitud"]),
            }
        lat = unit.get("latitud")
        lon = unit.get("longitud")
        if lat is None or lon is None:
            return None
        return {"latitud": float(lat), "longitud": float(lon)}
