"""Periodo con rango **opcional**, para los listados tacticos simples.

Es deliberadamente una implementacion aparte de `apps/informes_tacticos/periodo.py`
(research D1). Las diferencias no son cosmeticas:

| | `apps/informes_tacticos` | este modulo |
|---|---|---|
| Rango | **obligatorio** | **opcional** |
| `granularidad` | soportada | **rechazada** |
| Usado por | 19 informes agregados | los 64 listados |

El rango es opcional porque **un listado de estado actual no describe un
intervalo**. "Cuentas por estado" o "credenciales proximas a vencer" son el
ahora; exigirles un rango obligaria al consumidor a inventarse uno.

Y `granularidad` se rechaza en vez de ignorarse porque aqui no hay agrupacion
que granular: aceptarla en silencio le prometeria al consumidor un truncado por
mes que nadie va a hacer.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone


class PeriodoInvalido(ValueError):
    """El rango solicitado no es valido, o se declaro donde no se admite."""


class Periodo:
    """Rango [desde, hasta] en epoch milliseconds (UTC). Ambos extremos pueden faltar.

    `hasta` se interpreta **inclusiva**: el rango llega al ultimo milisegundo del
    dia solicitado. Es la lectura que espera quien pide "del 1 al 14": si `hasta`
    fuera exclusiva, los hechos del dia 14 no saldrian y nadie lo notaria hasta
    cuadrar cifras contra otra fuente.
    """

    def __init__(
        self,
        desde_ms: int | None = None,
        hasta_ms: int | None = None,
        desde: str | None = None,
        hasta: str | None = None,
    ):
        self.desde_ms = desde_ms
        self.hasta_ms = hasta_ms
        self.desde = desde
        self.hasta = hasta

    @property
    def vacio(self) -> bool:
        """True si no se declaro ningun extremo: el listado va sin acotar."""
        return self.desde_ms is None and self.hasta_ms is None

    def to_meta(self) -> dict:
        """Forma de `meta.filtros` para los extremos declarados.

        Un extremo ausente **no aparece** en vez de aparecer como `null`: `meta`
        refleja los filtros *aplicados*, y un extremo que no se aplico no es un
        filtro con valor nulo, es un filtro que no esta.
        """
        meta: dict = {}
        if self.desde is not None:
            meta["desde"] = self.desde
        if self.hasta is not None:
            meta["hasta"] = self.hasta
        return meta


def parse_periodo(query_params, *, admite_rango: bool = True) -> Periodo:
    """Construye un Periodo desde `desde`/`hasta`, ambos opcionales.

    `admite_rango=False` es el modo de los listados de **estado actual**: declarar
    cualquiera de los dos extremos es `400`. No se ignoran en silencio — un
    consumidor que cree haber filtrado por fecha y recibe el historico completo
    no tiene forma de notarlo (FR-012).

    `granularidad` se rechaza siempre: es de informes agregados y aqui no hay
    agrupacion (contrato comun §3.1).
    """
    desde_str = query_params.get("desde")
    hasta_str = query_params.get("hasta")

    if query_params.get("granularidad") is not None:
        raise PeriodoInvalido(
            "El parametro 'granularidad' no se admite en los listados: no hay agrupacion que granular."
        )

    if not admite_rango:
        declarados = [n for n, v in (("desde", desde_str), ("hasta", hasta_str)) if v]
        if declarados:
            raise PeriodoInvalido(
                f"Este listado describe el estado actual y no admite rango de fechas; "
                f"se recibio: {', '.join(declarados)}."
            )
        return Periodo()

    if not desde_str and not hasta_str:
        return Periodo()

    desde_date = _parse_fecha(desde_str, "desde") if desde_str else None
    hasta_date = _parse_fecha(hasta_str, "hasta") if hasta_str else None

    if desde_date and hasta_date and desde_date > hasta_date:
        raise PeriodoInvalido("'desde' no puede ser posterior a 'hasta'.")

    desde_ms = _a_epoch_ms(desde_date) if desde_date else None
    # 'hasta' inclusivo: hasta el ultimo milisegundo del dia solicitado.
    hasta_ms = (
        _a_epoch_ms(hasta_date + timedelta(days=1)) - 1 if hasta_date else None
    )

    return Periodo(desde_ms, hasta_ms, desde_str, hasta_str)


def parse_fecha_columna(
    query_params, nombre: str, *, inclusivo_al_final: bool = False
) -> int | None:
    """Lee un extremo `YYYY-MM-DD` de un filtro **de columna**, en epoch-ms.

    No todo rango de fechas es el periodo del contrato. Un listado de estado
    actual puede acotar una columna concreta —la fecha de cancelacion de una
    suscripcion, por ejemplo— sin convertirse en un listado de hechos del
    periodo: la tabla sigue guardando el estado de ahora, no un historico.

    `inclusivo_al_final` lleva el extremo al ultimo milisegundo del dia, la
    misma regla que `hasta` en el periodo. Si el extremo superior fuera
    exclusivo, los hechos del propio dia pedido no saldrian y nadie lo notaria
    sin cuadrar cifras contra otra fuente.
    """
    crudo = query_params.get(nombre)
    if not crudo:
        return None

    dia = _parse_fecha(crudo, nombre)
    inicio = _a_epoch_ms(dia)
    return inicio + 86_400_000 - 1 if inclusivo_al_final else inicio


def _parse_fecha(valor: str, nombre: str) -> date:
    try:
        return date.fromisoformat(valor)
    except ValueError as exc:
        raise PeriodoInvalido(
            f"El parametro '{nombre}' debe tener formato YYYY-MM-DD; se recibio '{valor}'."
        ) from exc


def _a_epoch_ms(dia: date) -> int:
    return int(datetime.combine(dia, time.min, tzinfo=timezone.utc).timestamp() * 1000)
