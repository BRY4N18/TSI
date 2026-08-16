"""Acceso de **solo lectura** al modelo analítico para los informes compuestos.

Un solo repositorio para todo el catálogo, no uno por informe. La diferencia con
el diseño anterior es deliberada: allí cada informe traía su repositorio y su
consulta incrustada en Python, y dos informes que medían lo mismo podían
calcularlo distinto sin que nada lo delatara. Aquí la consulta vive en su fichero
y este módulo solo la **ejecuta**.

Tres cosas que este repositorio garantiza y que no son comentarios
------------------------------------------------------------------

1. **No escribe.** Cada consulta va con `readonly=1`, así que la garantía la
   impone el servidor y no la buena voluntad de quien añade la siguiente. Un
   `INSERT` que se colara aquí falla en ClickHouse, no en una revisión.

2. **No concatena valores.** Los parámetros son los nativos de ClickHouse
   (`{desde:Date}` → `param_desde`), ligados por el servidor. Construir el rango
   con un f-string haría que un valor que contenga SQL **sea** SQL.

3. **Ausencia y cero no se mezclan.** Ver `_traducir_ausencia`.
"""

from __future__ import annotations

from typing import Any

from core.clickhouse.client import ClickHouseClient
from core.repositories.informes_tacticos.catalogo_consultas import cargar

#: Tope de tiempo del servidor. Un informe que tarda más no es un informe lento:
#: es un informe cuyo rango nadie acotó, y dejarlo correr bloquea el resto.
SEGUNDOS_MAXIMOS = 30

#: Ajustes que van con **toda** consulta del catálogo.
#:
#: `readonly=1` — la garantía de solo lectura la impone el servidor, no la buena
#: voluntad de quien añada la siguiente consulta.
#:
#: `output_format_json_quote_64bit_integers=0` — sin esto, ClickHouse devuelve
#: los enteros de 64 bits **entrecomillados**, y `count()` es `UInt64`: un conteo
#: de 1664 llega como la cadena `"1664"`. No falla en ninguna parte. La pantalla
#: lo pinta igual, porque pintar un número y pintar su texto se ven idénticos; y
#: solo se nota cuando algo intenta **sumarlos**, porque en JavaScript sumar dos
#: cadenas las concatena: dos períodos de 1664 y 1527 casos dan "16641527" en vez
#: de 3191. ClickHouse entrecomilla por defecto para no perder precisión por
#: encima de 2^53, que es un problema real para identificadores pero no para los
#: conteos y sumas de este catálogo.
AJUSTES = {
    "readonly": "1",
    "max_execution_time": str(SEGUNDOS_MAXIMOS),
    "output_format_json_quote_64bit_integers": "0",
}


class ModeloRepository:
    """Ejecuta consultas del catálogo contra el almacén analítico."""

    def __init__(self, client: ClickHouseClient | None = None):
        self._client = client or ClickHouseClient()

    def ejecutar(
        self,
        consulta: str,
        *,
        departamento: str,
        parametros: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Devuelve las filas del informe `consulta`, ya traducidas.

        `consulta` es el **nombre** de un fichero del catálogo, no SQL. No hay
        forma de pasar SQL por este método, que es justamente el punto: el
        catálogo es el conjunto cerrado de lo que se puede preguntar.
        """
        sql = cargar(consulta, departamento=departamento)
        filas = self._client.query(
            sql,
            params=parametros or {},
            settings=dict(AJUSTES),
        )
        return [_traducir_ausencia(fila) for fila in filas]


def _traducir_ausencia(fila: dict[str, Any]) -> dict[str, Any]:
    """Comprueba que la ausencia sale como nulo, y no la fabrica (FR-017).

    La ausencia y el cero se leen igual en una pantalla y significan lo
    contrario. Una completitud nula es *«este período no tuvo casos, no hay
    porcentaje que dar»*; una completitud de `0` es *«hubo casos y ninguno estaba
    completo»*. La primera no es una alarma; la segunda lo es.

    Aquí **no hay traducción que hacer**, y eso se verificó en vez de suponerse:
    ClickHouse emite `null` en `JSONEachRow` tanto para `NULL` como para los
    denormales `NaN` e `Inf` —lo hace por defecto, con
    `output_format_json_quote_denormals=0`—, así que lo que llega ya distingue
    ausencia de cero. Se comprobó por la ruta real, HTTP desde el contenedor de
    Django: `SELECT 1/0, 0/0, NULL` devuelve `{"inf":null,"nan":null,"nulo":null}`.

    Lo que esta función impide es lo contrario: que alguien añada aquí un
    `or 0`, un `fillna` o un `valor if valor else 0` para «limpiar» la respuesta.
    Ese relleno es la forma en que la distinción se pierde, y se pierde en
    silencio — la pantalla sigue pintando un número, solo que el equivocado.

    Si algún día hiciera falta normalizar de verdad, va aquí y con su prueba.
    """
    return dict(fila)
