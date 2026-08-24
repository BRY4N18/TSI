"""Recarga de un período: descartar su partición y repoblarla.

Por qué no se borra por condición  ⚠️
-------------------------------------
Los flujos del diseño anterior son idempotentes, y lo consiguen con
`ALTER TABLE … DELETE WHERE periodo IN (…)` antes de insertar. Funciona, pero en
este almacén ese borrado es una **mutación**: una operación asíncrona y pesada
que reescribe partes enteras de la tabla. Con tres informes y una corrida diaria
se tolera; con **13 hechos** cargándose con regularidad las mutaciones se
acumulan y compiten entre sí (research D3).

Descartar una partición, en cambio, es una operación de metadatos: instantánea y
sin reescritura. Es el mecanismo idiomático del almacén para exactamente este
caso, y convierte la idempotencia en una **propiedad de la estructura** en vez de
en un paso costoso que hay que acordarse de hacer bien.

Por eso este módulo **no emite borrados por condición**, y hay una prueba que lo
verifica: la tentación de «solo por esta vez» es justo cómo volvería.

Lo que esto NO es
-----------------
**El descarte y la inserción no son atómicos.** Entre uno y otro, una consulta
sobre ese período ve cero filas. Es aceptable para carga analítica programada —
nadie consulta un informe táctico en el instante de su recarga— pero conviene
saberlo antes de reutilizar este módulo para algo que se consulte en vivo.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime
from typing import Any, Callable, Iterable, Mapping, Sequence

from lib.clickhouse_http_client import execute_clickhouse, insert_rows


def particion_de(momento: date | datetime | str) -> int:
    """Partición mensual a la que pertenece una fecha: `toYYYYMM`.

    Acepta texto porque las filas ya serializadas para el almacén llevan la
    fecha como cadena, y obligar a quien llama a reconvertirla invitaría a que
    cada flujo lo hiciera a su manera.
    """
    if isinstance(momento, str):
        momento = datetime.fromisoformat(momento)
    return momento.year * 100 + momento.month


def cargar_particiones(
    tabla: str,
    filas: Sequence[Mapping[str, Any]],
    *,
    campo_fecha: str = "fecha",
    particiones_vacias: Iterable[int] = (),
    ejecutar: Callable[[str], None] = execute_clickhouse,
    insertar: Callable[[str, list[dict]], None] = insert_rows,
) -> list[int]:
    """Repuebla, de forma idempotente, las particiones que tocan estas filas.

    Recargar el mismo período deja **el mismo número exacto de filas**, no el
    doble: la partición se descarta antes de insertar.

    `particiones_vacias` cubre un caso que se olvida y corrompe en silencio: si
    un período que antes tenía filas pasa a no tener ninguna, sin nombrarlo
    explícitamente nadie descartaría su partición y **las filas viejas
    sobrevivirían** a una recarga que debía dejarlo vacío.

    `ejecutar` e `insertar` se inyectan para poder comprobar en una prueba **qué
    SQL se emite**, que es la única forma de verificar que no aparece un borrado
    por condición.

    Devuelve las particiones tocadas, en orden.

    ⚠️ **La carga NO es atomica, y conviene saberlo antes de confiar en ella.**
    `DROP PARTITION` e `INSERT` son dos operaciones y ClickHouse no ofrece
    transaccion entre ambas: si la insercion falla, la particion queda **vacia**,
    no a medias.

    Vacia es menos malo que parcial —el cuadre de `PG-ANA-001` lo ve como
    «faltan N» y lo reporta, mientras que unas cuantas filas de menos pasarian
    por un mes flojo— pero sigue siendo una ventana en la que el informe muestra
    cero para un periodo que tenia datos.

    Se documenta aqui, donde vive el codigo, para que nadie suponga una garantia
    que el motor no da (PG-ANA-003).
    """
    por_particion: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for fila in filas:
        por_particion[particion_de(fila[campo_fecha])].append(dict(fila))

    for vacia in particiones_vacias:
        por_particion.setdefault(int(vacia), [])

    for particion in sorted(por_particion):
        ejecutar(f"ALTER TABLE {tabla} DROP PARTITION {particion}")
        if por_particion[particion]:
            insertar(tabla, por_particion[particion])

    return sorted(por_particion)
