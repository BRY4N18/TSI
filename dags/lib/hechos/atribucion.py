"""Atribución histórica: a qué versión de una entidad pertenece un hecho.

Vive aparte porque **más de un hecho la necesita**. `hecho_despacho` la usa para
saber de qué proveedor era la unidad al despachar, y `hecho_estado_unidad` para
lo mismo al registrar un cambio de estado.

La alternativa —que el segundo hecho importara la función privada del primero—
crearía una dependencia entre hechos que no existe en el modelo: son dos tablas
independientes que comparten una dimensión, no una que dependa de la otra. Esa
dependencia falsa se notaría el día que uno de los dos se retirara.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Iterable, Mapping

from lib.dimensiones.versionado import version_vigente_en
from lib.hechos.comun import FORMATO


def versiones_por_unidad(filas: Iterable[Mapping[str, Any]]) -> dict[int, list[dict]]:
    """Versiones de cada unidad, con sus fechas ya convertidas.

    El almacén devuelve las fechas como texto; compararlas sin convertir haría
    que `2099-12-05` fuese «menor» que `2100-01-01` por casualidad del orden
    alfabético, y fallaría en cuanto una fecha cambiara de longitud.
    """
    por_unidad: dict[int, list[dict]] = {}
    for fila in filas:
        version = dict(fila)
        for campo in ("valido_desde", "valido_hasta"):
            valor = version.get(campo)
            if isinstance(valor, str):
                version[campo] = datetime.strptime(valor, FORMATO)
        # ⚠️ El almacén serializa `UInt64` **como texto** para no perder precisión
        # en clientes con enteros de 53 bits. Si no se convierte aquí, la clave
        # llega al hecho como cadena y se mezcla con el `0` entero de la versión
        # desconocida: la columna queda de tipo mixto y la escritura del fichero
        # intermedio falla — con un error que habla de conversión, no de esto.
        sk = version.get("sk_unidad")
        if sk is not None:
            version["sk_unidad"] = int(sk)
        por_unidad.setdefault(version["idunidademergencia"], []).append(version)
    return por_unidad


def resolver_unidad_historica(
    versiones_por_unidad: Mapping[int, list[Mapping[str, Any]]],
    idunidad: int | None,
    instante: datetime,
) -> Mapping[str, Any] | None:
    """La versión de esa unidad vigente en ese instante. `None` si no hay ninguna.

    Devolver `None` en vez de la versión actual es lo que impide reintroducir el
    defecto: quien llama apunta entonces a la versión desconocida, que es
    información honesta, en lugar de a una atribución inventada.
    """
    if idunidad is None:
        return None
    return version_vigente_en(versiones_por_unidad.get(idunidad, []), instante)
