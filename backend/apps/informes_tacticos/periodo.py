"""Parseo y validación del filtro de período compartido por los 16 informes.

FR-002/FR-003 de la spec: el rango de fechas es obligatorio, la granularidad
determina la expresión DATETRUNC que cada repositorio usa en su SQL — el
truncado de fecha vive en Pinot (SQL), nunca se agrupa en Python.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone

GRANULARIDADES = {"dia": "day", "semana": "week", "mes": "month"}
GRANULARIDAD_DEFAULT = "dia"


class PeriodoInvalido(ValueError):
    """El rango o la granularidad solicitados no son válidos."""


class Periodo:
    """Rango [desde, hasta] en epoch milliseconds (UTC), más granularidad Pinot."""

    def __init__(self, desde_ms: int, hasta_ms: int, granularidad: str, desde: str, hasta: str):
        self.desde_ms = desde_ms
        self.hasta_ms = hasta_ms
        self.granularidad = granularidad
        self.desde = desde
        self.hasta = hasta

    @property
    def datetrunc_unit(self) -> str:
        return GRANULARIDADES[self.granularidad]

    def to_meta(self) -> dict:
        return {
            "desde": self.desde,
            "hasta": self.hasta,
            "granularidad": self.granularidad,
        }


def parse_periodo(query_params) -> Periodo:
    """Construye un Periodo desde los query params `desde`/`hasta`/`granularidad`.

    `desde`/`hasta` son fechas ISO (YYYY-MM-DD); `hasta` se interpreta inclusiva
    (fin del día). Lanza PeriodoInvalido si falta un parámetro obligatorio, el
    formato es incorrecto, el rango está invertido, o la granularidad no es una
    de las soportadas.
    """
    desde_str = query_params.get("desde")
    hasta_str = query_params.get("hasta")
    granularidad = query_params.get("granularidad", GRANULARIDAD_DEFAULT)

    if not desde_str or not hasta_str:
        raise PeriodoInvalido("Los parámetros 'desde' y 'hasta' son obligatorios.")

    if granularidad not in GRANULARIDADES:
        raise PeriodoInvalido(
            f"granularidad '{granularidad}' no soportada, use una de: {sorted(GRANULARIDADES)}."
        )

    try:
        desde_date = date.fromisoformat(desde_str)
        hasta_date = date.fromisoformat(hasta_str)
    except ValueError as exc:
        raise PeriodoInvalido("Las fechas deben tener formato YYYY-MM-DD.") from exc

    if desde_date > hasta_date:
        raise PeriodoInvalido("'desde' no puede ser posterior a 'hasta'.")

    desde_dt = datetime.combine(desde_date, time.min, tzinfo=timezone.utc)
    # 'hasta' inclusivo: fin del día solicitado, un milisegundo antes del día siguiente.
    hasta_dt = datetime.combine(hasta_date + timedelta(days=1), time.min, tzinfo=timezone.utc)
    desde_ms = int(desde_dt.timestamp() * 1000)
    hasta_ms = int(hasta_dt.timestamp() * 1000) - 1

    return Periodo(desde_ms, hasta_ms, granularidad, desde_str, hasta_str)
