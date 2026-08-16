"""Ajusta las filas al tipo que declara la tabla destino, antes de insertar.

Por qué hace falta ⚠️
---------------------
El paso por parquet **cambia los tipos**. Pandas no tiene enteros ausentes en una
columna de enteros: si una sola fila trae `capacidad` ausente, la columna entera
pasa a decimal y un `4` se convierte en `4.0`. El almacén entonces rechaza la
inserción con un error de análisis sintáctico que señala la posición del carácter
—no la columna, ni mucho menos la causa—, y cuesta media hora entender que el
problema ocurrió tres pasos antes.

Por qué se lee el esquema en vez de adivinar
---------------------------------------------
La tentación es convertir a entero todo decimal cuya parte fraccionaria sea cero.
Funciona hoy, porque en esta fase ninguna columna del modelo es fraccionaria — y
**deja puesta una trampa** para la primera métrica decimal que se añada: un
promedio de 4.0 se guardaría como 4, y nadie lo notaría hasta comparar cifras.

Leer el tipo declarado no tiene ese problema: la autoridad es la tabla.

La ausencia se respeta siempre
------------------------------
Un valor ausente sigue ausente sea cual sea el tipo de la columna. Convertirlo a
cero para «encajar» reintroduciría el defecto que el modelo entero combate.
"""

from __future__ import annotations

from typing import Any, Callable, Iterable, Mapping

from lib.clickhouse_http_client import query_clickhouse

_CACHE: dict[str, dict[str, str]] = {}


def tipos_de(tabla: str, consultar: Callable[[str], list[dict]] = query_clickhouse) -> dict[str, str]:
    """Columna → tipo declarado. Se consulta una vez por tabla y corrida."""
    if tabla not in _CACHE:
        filas = consultar(
            "SELECT name, type FROM system.columns "
            f"WHERE database = currentDatabase() AND table = '{tabla}'"
        )
        _CACHE[tabla] = {f["name"]: f["type"] for f in filas}
    return _CACHE[tabla]


def _ajustar(valor: Any, tipo: str) -> Any:
    if valor is None:
        return None
    base = tipo.replace("Nullable(", "").rstrip(")")
    if base.startswith(("Int", "UInt")):
        return int(valor)
    if base.startswith(("Float", "Decimal")):
        return float(valor)
    if base.startswith(("String", "Date", "DateTime", "Enum")):
        return valor if isinstance(valor, str) else str(valor)
    return valor


def ajustar_tipos(
    tabla: str,
    filas: Iterable[Mapping[str, Any]],
    consultar: Callable[[str], list[dict]] = query_clickhouse,
) -> list[dict[str, Any]]:
    """Filas listas para insertar en `tabla`.

    Las columnas que la tabla no declara **se descartan**: llegar con una columna
    de más aborta la inserción entera, y una columna sobrante en el fichero
    intermedio no es motivo para perder la carga del período.
    """
    tipos = tipos_de(tabla, consultar)
    return [
        {clave: _ajustar(valor, tipos[clave]) for clave, valor in fila.items() if clave in tipos}
        for fila in filas
    ]
