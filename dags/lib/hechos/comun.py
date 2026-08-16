"""Piezas que los dos hechos comparten: tiempo, franjas y desnormalización.

Vive aquí y no duplicado en cada hecho porque **la franja horaria y el formato
de fecha tienen que coincidir entre hechos**. Si `hecho_accidente` llamara
«mañana» a las 6:00 y `hecho_despacho` a las 7:00, dos informes que parecen medir
lo mismo darían cifras distintas y nadie sabría cuál creer.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable, Mapping

FORMATO = "%Y-%m-%d %H:%M:%S"

#: Cortes de franja horaria, en horas. El día empieza en la madrugada.
FRANJAS = ((0, "madrugada"), (6, "manana"), (12, "tarde"), (18, "noche"))


def a_datetime(epoch_ms: int | None) -> datetime | None:
    """Milisegundos de época → fecha. **Ausente sigue ausente.**

    El cliente del origen ya convierte los centinelas de nulo a `None`; aquí solo
    hay que no reintroducirlos. Devolver la época cero ante un valor ausente
    convertiría «no ocurrió» en «ocurrió en 1970».
    """
    if epoch_ms is None:
        return None
    return datetime.fromtimestamp(epoch_ms / 1000, tz=timezone.utc).replace(tzinfo=None)


def texto_fecha(momento: datetime | None) -> str | None:
    return momento.strftime(FORMATO) if momento is not None else None


def franja_horaria(momento: datetime) -> str:
    nombre = FRANJAS[0][1]
    for hora, etiqueta in FRANJAS:
        if momento.hour >= hora:
            nombre = etiqueta
    return nombre


def segundos_entre(desde: datetime | None, hasta: datetime | None) -> int | None:
    """Diferencia en segundos, o ausente si falta cualquiera de los dos extremos.

    **Ausente, no cero.** Un tránsito que nunca terminó no duró cero segundos, y
    un promedio que lo cuente como cero se hunde sin que nadie vea por qué.
    """
    if desde is None or hasta is None:
        return None
    return int((hasta - desde).total_seconds())


def indexar_por(filas: Iterable[Mapping[str, Any]], clave: str) -> dict[Any, Mapping[str, Any]]:
    return {f[clave]: f for f in filas}


def agrupar_por(filas: Iterable[Mapping[str, Any]], clave: str) -> dict[Any, list[Mapping[str, Any]]]:
    grupos: dict[Any, list[Mapping[str, Any]]] = {}
    for fila in filas:
        grupos.setdefault(fila[clave], []).append(fila)
    return grupos
