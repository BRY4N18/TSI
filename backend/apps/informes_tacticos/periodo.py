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


#: Ventana por defecto de los informes compuestos, en días.
DIAS_POR_DEFECTO = 30


def parse_periodo_con_defecto(query_params, *, hoy: date | None = None) -> Periodo:
    """Como `parse_periodo`, pero el rango es **opcional**: por defecto, 30 días.

    Los 16 listados simples exigen el rango porque quien los consulta viene de un
    filtro. Los compuestos se abren desde un panel y tienen que mostrar algo, así
    que traen una ventana por defecto.

    ⚠️ **Los 30 días incluyen hoy**, así que el rango es `[hoy-29, hoy]` y no
    `[hoy-30, hoy]`. Restar 30 daría 31 días contando ambos extremos: el error
    clásico de poste y valla. No falla ni se ve —el informe sale, con un día de
    más—, pero basta para que dos períodos «de 30 días» consecutivos compartan
    una jornada y las sumas no cuadren con el total.

    Si el rango viene dado, se valida igual que en los listados simples: un rango
    inválido es un error, nunca un silencioso vuelta-al-defecto.
    """
    desde = query_params.get("desde")
    hasta = query_params.get("hasta")

    if not desde and not hasta:
        fin = hoy or datetime.now(timezone.utc).date()
        inicio = fin - timedelta(days=DIAS_POR_DEFECTO - 1)
        query_params = dict(query_params)
        query_params["desde"] = inicio.isoformat()
        query_params["hasta"] = fin.isoformat()

    return parse_periodo(query_params)


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
