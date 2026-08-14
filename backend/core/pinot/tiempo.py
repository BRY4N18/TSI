"""Marcas de tiempo para los payloads que se publican hacia Pinot.

Todas las tablas del proyecto declaran `fecha_actualizacion` como
`LONG` con formato `1:MILLISECONDS:EPOCH`, y en la mayoría es además la
**columna de tiempo** de la tabla y la columna de comparación del upsert.

Publicar ahí una cadena ISO-8601 no produce ningún error: Pinot **descarta la
fila en silencio**. El escritor recibe un 201, el usuario ve la operación como
exitosa y el registro no existe. Por eso esta función es la única forma correcta
de sellar un payload, y ningún repositorio debe volver a llamar a `isoformat()`
para este campo.
"""

from __future__ import annotations

from datetime import datetime, timezone


def ahora_ms() -> int:
    """Instante actual en milisegundos desde epoch (UTC)."""
    return int(datetime.now(timezone.utc).timestamp() * 1000)


# Centinela de "sin fecha" para columnas dateTime opcionales.
#
# Pinot no almacena NULL en este proyecto: ninguna tabla habilita
# `nullHandlingEnabled`. Una columna dateTime sin valor termina siendo
# `Long.MIN_VALUE`, que es lo que ya llevan las filas sembradas. Publicar ese
# valor explícitamente evita la alternativa que causó el fallo — mandar `""`,
# que hace que Pinot descarte la fila entera sin avisar.
SIN_FECHA = -9223372036854775808


def mes_anio_a_ms(valor: str | None) -> int:
    """Convierte una expiración `MM/AA` (o `MM/AAAA`) a epoch en milisegundos.

    Una tarjeta con expiración `12/30` es válida **hasta el final** de diciembre
    de 2030, así que se sella el último milisegundo del mes.

    `fechaexpiracion` es una columna `LONG` epoch-millis. Publicar ahí el texto
    del formulario tal cual hace que Pinot descarte la fila entera sin avisar
    (mismo fallo que documenta el módulo). Cualquier valor que no se pueda
    interpretar devuelve `SIN_FECHA` en vez de propagar la cadena.
    """
    if not valor:
        return SIN_FECHA
    partes = str(valor).strip().split("/")
    if len(partes) != 2:
        return SIN_FECHA
    try:
        mes = int(partes[0])
        anio = int(partes[1])
    except ValueError:
        return SIN_FECHA
    if not 1 <= mes <= 12:
        return SIN_FECHA
    if anio < 100:  # `30` significa 2030
        anio += 2000
    mes_siguiente = datetime(
        anio + (1 if mes == 12 else 0),
        1 if mes == 12 else mes + 1,
        1,
        tzinfo=timezone.utc,
    )
    return int(mes_siguiente.timestamp() * 1000) - 1
