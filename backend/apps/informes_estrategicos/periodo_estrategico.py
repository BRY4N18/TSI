"""Período obligatorio de la capa estratégica.

Es la regla inversa a la de los listados tácticos: allí el rango puede omitirse
porque la mitad describe el estado actual; aquí un agregado sin período no es un
número peor, no es un número. Por eso este módulo **no** reutiliza
`informes_tacticos/periodo.py`.

La granularidad se traduce desde una lista cerrada. El nombre de la función de
truncado vive **dentro** de cada consulta; un valor libre interpolado en el SQL
sería inyección.
"""

from __future__ import annotations

from calendar import monthrange
from datetime import date, datetime, timedelta, timezone
from typing import Any

GRANULARIDADES = ("mes", "trimestre", "anio")
COMPARACIONES = ("ninguna", "mom", "yoy")

#: Nombre de la función de ClickHouse que corresponde a cada granularidad.
#: Se documenta aquí para quien lea el servicio; **no se interpola en el SQL**.
FUNCION_TRUNCADO = {
    "mes": "toStartOfMonth",
    "trimestre": "toStartOfQuarter",
    "anio": "toStartOfYear",
}

MOTIVO_SIN_VENTANA_ANTERIOR = (
    "No hay datos en la ventana anterior (el histórico arranca en 2026-02-03)."
)


class PeriodoEstrategicoInvalido(ValueError):
    """Falta un parámetro obligatorio, o un valor de enumeración no se reconoce."""


class PeriodoEstrategico:
    """Rango [desde, hasta] inclusive, con granularidad y marca de período en curso."""

    def __init__(
        self,
        desde: date,
        hasta: date,
        granularidad: str,
        *,
        parcial: bool,
    ):
        self.desde = desde
        self.hasta = hasta
        self.granularidad = granularidad
        self.parcial = parcial

    @property
    def longitud_dias(self) -> int:
        return (self.hasta - self.desde).days + 1

    def to_meta(self) -> dict[str, Any]:
        return {
            "desde": self.desde.isoformat(),
            "hasta": self.hasta.isoformat(),
            "granularidad": self.granularidad,
            "parcial": self.parcial,
        }

    def to_params(self) -> dict[str, Any]:
        return {
            "desde": self.desde.isoformat(),
            "hasta": self.hasta.isoformat(),
            "granularidad": self.granularidad,
        }

    def ventana_anterior(self, tipo: str) -> PeriodoEstrategico:
        """Desplaza esta ventana conservando su longitud.

        `mom` termina el día anterior a `desde`. `yoy` retrocede un año civil y
        ajusta el extremo para que ambos rangos midan los mismos días: comparar
        11 días contra 30 publica una caída del 63 % que no ocurrió.
        """
        if tipo == "mom":
            hasta = self.desde - timedelta(days=1)
            desde = hasta - timedelta(days=self.longitud_dias - 1)
        elif tipo == "yoy":
            desde = _menos_un_anio(self.desde)
            hasta = desde + timedelta(days=self.longitud_dias - 1)
        else:
            raise PeriodoEstrategicoInvalido(
                f"comparacion '{tipo}' no soportada, use una de: {list(COMPARACIONES)}."
            )
        return PeriodoEstrategico(
            desde, hasta, self.granularidad, parcial=False
        )


def parse_periodo_estrategico(
    query_params,
    *,
    hoy: date | None = None,
) -> PeriodoEstrategico:
    """Construye el período desde `desde` / `hasta` / `granularidad`.

    Los tres son **obligatorios**. Omitir cualquiera responde nombrando cuál
    falta; una granularidad desconocida lista las válidas. Nunca se sustituye
    en silencio por un defecto.
    """
    desde_str = query_params.get("desde")
    hasta_str = query_params.get("hasta")
    granularidad = query_params.get("granularidad")

    faltan = [
        nombre
        for nombre, valor in (
            ("desde", desde_str),
            ("hasta", hasta_str),
            ("granularidad", granularidad),
        )
        if not valor
    ]
    if faltan:
        if len(faltan) == 1:
            raise PeriodoEstrategicoInvalido(
                f"El parámetro '{faltan[0]}' es obligatorio."
            )
        citados = ", ".join(f"'{n}'" for n in faltan)
        raise PeriodoEstrategicoInvalido(
            f"Los parámetros {citados} son obligatorios."
        )

    if granularidad not in GRANULARIDADES:
        raise PeriodoEstrategicoInvalido(
            f"granularidad '{granularidad}' no soportada, use una de: "
            f"{list(GRANULARIDADES)}."
        )

    try:
        desde = date.fromisoformat(str(desde_str))
        hasta = date.fromisoformat(str(hasta_str))
    except ValueError as exc:
        raise PeriodoEstrategicoInvalido(
            "Las fechas deben tener formato YYYY-MM-DD."
        ) from exc

    if desde > hasta:
        raise PeriodoEstrategicoInvalido("'desde' no puede ser posterior a 'hasta'.")

    hoy = hoy or datetime.now(timezone.utc).date()
    parcial = hasta >= hoy
    return PeriodoEstrategico(desde, hasta, granularidad, parcial=parcial)


def parse_comparacion(query_params) -> str:
    valor = query_params.get("comparacion") or "ninguna"
    if valor not in COMPARACIONES:
        raise PeriodoEstrategicoInvalido(
            f"comparacion '{valor}' no soportada, use una de: {list(COMPARACIONES)}."
        )
    return valor


def _menos_un_anio(dia: date) -> date:
    try:
        return dia.replace(year=dia.year - 1)
    except ValueError:
        # 29 de febrero: el año anterior no lo tiene. Se toma el último día
        # de febrero para no alargar la ventana en silencio.
        ultimo = monthrange(dia.year - 1, 2)[1]
        return date(dia.year - 1, 2, ultimo)
