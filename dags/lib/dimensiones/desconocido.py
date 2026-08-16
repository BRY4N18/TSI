"""La fila «desconocida» de cada dimensión: a dónde apunta un hecho huérfano.

El problema  ⚠️
---------------
Un accidente llega con una calle que no está en el catálogo. Hay tres salidas
posibles y solo una es aceptable:

1. **Descartar el hecho** — se pierde un accidente del análisis porque falta una
   calle en un catálogo. Inaceptable: el hecho es el dato valioso, la dimensión
   es su etiqueta.
2. **Dejar la referencia en nulo** — el hecho sobrevive, pero toda unión con la
   dimensión lo hace desaparecer igualmente, y de forma silenciosa. Es el mismo
   defecto con más pasos.
3. **Apuntar a una fila «desconocida» que sí existe** — el hecho se conserva, las
   uniones lo devuelven, y las cifras muestran «Desconocido» en vez de callarse.

Este módulo implementa la tercera.

Por qué el hecho se carga igualmente
------------------------------------
El origen es un sistema en vivo con retraso de ingesta: una calle registrada hace
diez segundos puede no estar visible cuando el flujo la busque. La ausencia suele
ser **temporal**, y un diseño que descarte hechos ante una ausencia temporal
pierde datos de forma permanente por un problema pasajero.

Cuando la dimensión aparezca, la recarga del período volverá a resolverla: la
referencia a la fila desconocida es una respuesta provisional, no un veredicto.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Iterable, Mapping

#: Las fechas se emiten **como texto**, igual que en los módulos de cada
#: dimensión. No es cosmético: estas filas se concatenan con las de su dimensión
#: antes de pasar por parquet, y una columna con fechas y textos mezclados falla
#: la conversión — con un error que apunta al fichero, no a la mezcla.
FORMATO = "%Y-%m-%d %H:%M:%S"

#: Clave desconocida de las dimensiones con clave entera con signo. Se usa `-1` y
#: no `0` porque `0` es un identificador válido en varios catálogos del origen.
ID_DESCONOCIDO = -1

#: Clave sustituta desconocida de las dimensiones versionadas. Aquí sí es `0`:
#: la columna es `UInt64` y no admite negativos, y `sk_de_version` nunca lo emite.
SK_DESCONOCIDO = 0

#: Etiqueta única. Que aparezca en un informe **es información**, no un fallo:
#: dice que el hecho existe y su dimensión no se pudo resolver.
ETIQUETA_DESCONOCIDA = "Desconocido"


def fila_desconocida_geografia(ahora: datetime) -> dict[str, Any]:
    return {
        "idcalle": ID_DESCONOCIDO,
        "calle": ETIQUETA_DESCONOCIDA,
        "idciudad": ID_DESCONOCIDO,
        "ciudad": ETIQUETA_DESCONOCIDA,
        "idcondado": ID_DESCONOCIDO,
        "condado": ETIQUETA_DESCONOCIDA,
        "idestado": ID_DESCONOCIDO,
        "estado": ETIQUETA_DESCONOCIDA,
        "idpais": ID_DESCONOCIDO,
        "pais": ETIQUETA_DESCONOCIDA,
        "version": ahora.strftime(FORMATO),
    }


def fila_desconocida_severidad(ahora: datetime) -> dict[str, Any]:
    return {
        "idseveridad": ID_DESCONOCIDO,
        "severidad": ETIQUETA_DESCONOCIDA,
        "descripcion": None,
        # Orden alto: al ordenar por gravedad, lo no clasificado queda al final y
        # no se cuela entre lo crítico y lo leve fingiendo una gravedad que nadie
        # determinó.
        "orden": 255,
        "version": ahora.strftime(FORMATO),
    }


def fila_desconocida_origen_despacho(ahora: datetime) -> dict[str, Any]:
    return {
        "idorigendespacho": ID_DESCONOCIDO,
        "origen": ETIQUETA_DESCONOCIDA,
        "version": ahora.strftime(FORMATO),
    }


def fila_desconocida_unidad(ahora: datetime) -> dict[str, Any]:
    """Versión desconocida de unidad.

    `inicio_es_real = 0`: no se sabe nada de esta unidad, y menos aún desde
    cuándo. Declararlo real sería la mentira exacta que la marca existe para
    evitar.

    `valido_desde` es la época cero **a propósito, y solo aquí**: esta versión
    debe cubrir cualquier instante consultado, incluido el anterior a la primera
    carga. Es la única fila del modelo donde una fecha centinela es correcta,
    porque no representa un suceso sino un intervalo abierto por la izquierda.
    """
    return {
        "sk_unidad": SK_DESCONOCIDO,
        "idunidademergencia": ID_DESCONOCIDO,
        "placa": ETIQUETA_DESCONOCIDA,
        "nombre_unidad": None,
        "tipo_unidad": None,
        "capacidad": None,
        "idcliente": ID_DESCONOCIDO,
        "proveedor": ETIQUETA_DESCONOCIDA,
        "idcondado": None,
        "condado": None,
        "zona_cobertura": None,
        "valido_desde": datetime(1970, 1, 1).strftime(FORMATO),
        "valido_hasta": None,
        "es_vigente": 1,
        "inicio_es_real": 0,
        "version": ahora.strftime(FORMATO),
    }


#: Tabla → constructor de su fila desconocida. `dim_tiempo` **no aparece**: se
#: genera completa a partir de un rango de fechas, así que no puede faltarle una
#: fila; un hecho sin fecha no es un hecho.
FILAS_DESCONOCIDAS = {
    "dim_geografia": fila_desconocida_geografia,
    "dim_severidad": fila_desconocida_severidad,
    "dim_origen_despacho": fila_desconocida_origen_despacho,
    "dim_unidad": fila_desconocida_unidad,
}


def resolver_o_desconocido(
    clave: Any,
    conocidas: Mapping[Any, Any] | Iterable[Any],
    *,
    desconocida: Any = ID_DESCONOCIDO,
) -> Any:
    """Devuelve **la clave**, o la desconocida si la dimensión no la tiene.

    Devuelve la clave y no el valor asociado a propósito: `conocidas` suele ser
    el índice de la dimensión —clave → fila entera—, y devolver el valor
    metería la fila completa dentro de una columna del hecho. Lo que el hecho
    necesita es una referencia que **una**, y eso es la clave.

    **Nunca lanza y nunca devuelve nulo.** Es lo que garantiza que quien carga un
    hecho no tenga que decidir, caso por caso, qué hacer ante una dimensión que
    falta — y que la respuesta no dependa de quién escribió ese flujo.
    """
    if clave is None:
        return desconocida
    return clave if clave in conocidas else desconocida
