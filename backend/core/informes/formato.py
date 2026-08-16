"""Presentacion de valores en los listados tacticos.

Vive en `core/informes/` y no en la app de un departamento porque los 64
listados devuelven las mismas marcas de tiempo desde las mismas columnas `LONG`
epoch-millis, y porque la regla de FR-021 —**ausencia no es cero**— tiene que
significar lo mismo en los ocho departamentos.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


#: Centinelas con los que Pinot representa "sin valor" en columnas INT y LONG,
#: porque ninguna tabla del proyecto habilita `nullHandlingEnabled`.
#: `core/pinot/client.py:_coerce_value` ya los convierte a `None` al leer, así
#: que por la vía normal aquí llega `None` limpio. La comprobación se repite
#: igualmente porque **el doble en memoria de las pruebas no coerciona**, y sin
#: ella un centinela se convertiría en «hace 106.752.011.843 días» — un número
#: absurdo, pero que ninguna comprobación de tipo rechazaría.
_CENTINELAS = (-9223372036854775808, -2147483648)


def marca_ausente(epoch_ms: Any) -> bool:
    """True si la marca de tiempo no lleva valor, en cualquiera de sus formas.

    Existe para que las dos lecturas de una misma columna —la fecha que se
    muestra y los días que se calculan desde ella— **no puedan discrepar**. Si
    cada una decidiera por su cuenta qué es ausencia, una fila podría salir con
    la fecha en `null` y a la vez con una antigüedad calculada, que es
    contradictorio y difícil de explicar.
    """
    if epoch_ms is None or epoch_ms == "":
        return True
    try:
        return int(epoch_ms) in _CENTINELAS
    except (TypeError, ValueError):
        return True


def a_entero_ms(epoch_ms: Any) -> int | None:
    """La marca como entero, o `None` si está ausente."""
    return None if marca_ausente(epoch_ms) else int(epoch_ms)


def a_iso(epoch_ms: Any) -> str | None:
    """Convierte una marca `LONG` epoch-millis a ISO-8601 UTC, o `None`.

    Un valor ausente devuelve `None`, **nunca la epoca ni la fecha de carga**
    (FR-021). Devolver `1970-01-01` para un hito que no ocurrio es peor que no
    devolver nada: es una fecha creible que nadie va a cuestionar.
    """
    valor = a_entero_ms(epoch_ms)
    if valor is None:
        return None
    return datetime.fromtimestamp(valor / 1000, tz=timezone.utc).isoformat()


def a_fecha(epoch_ms: Any) -> str | None:
    """Igual que `a_iso` pero solo la parte de fecha, para campos `format: date`."""
    iso = a_iso(epoch_ms)
    return iso[:10] if iso else None
