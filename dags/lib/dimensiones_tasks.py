"""Tareas del flujo de dimensiones (T019).

Viven aquí y no en el fichero del DAG por la misma razón que las de los tres
flujos anteriores: así otro DAG puede reutilizarlas sin importar un fichero de
DAG desde otro fichero de DAG.

**Este flujo debe correr antes que cualquier flujo de hechos.** No es una
preferencia de orden: los hechos copian severidad, condado y proveedor **desde
las dimensiones ya cargadas**, y sin ellas cargarían esas columnas vacías.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from lib.clickhouse_http_client import insert_rows, query_clickhouse
from lib.ddl import ensure_modelo_analitico
from lib.dimensiones import dim_geografia, dim_origen_despacho, dim_severidad, dim_tiempo, dim_unidad
from lib.dimensiones.desconocido import FILAS_DESCONOCIDAS
from lib.etl_modelo import cargar, guardar, ruta
from lib.hechos.comun import a_datetime
from lib.pinot_http_client import query_pinot
from lib.tipos_almacen import ajustar_tipos

FLUJO = "dimensiones"

#: Margen del calendario alrededor de los datos observados. Genera días que aún
#: no tienen actividad **a propósito**: un informe del mes en curso debe poder
#: mostrar sus días vacíos como vacíos, no como ausentes.
MARGEN_DIAS = 400

DIMENSIONES = ("dim_tiempo", "dim_geografia", "dim_severidad", "dim_origen_despacho", "dim_unidad")


def _prefijo(nombre: str) -> str:
    return f"{FLUJO}_{nombre}_"


def _ahora() -> datetime:
    return datetime.now(tz=timezone.utc).replace(tzinfo=None, microsecond=0)


def extract(ts: str, **_) -> None:
    """Trae los catálogos del origen y las versiones de unidad ya cargadas."""
    ensure_modelo_analitico()

    catalogos = dim_geografia.extraer()
    for nombre, filas in catalogos.items():
        guardar(filas, ruta(ts, "extract", _prefijo(nombre)))

    guardar(dim_severidad.extraer(), ruta(ts, "extract", _prefijo("severidad")))
    guardar(dim_origen_despacho.extraer(), ruta(ts, "extract", _prefijo("origen")))

    unidades, clientes, condados, vigentes = dim_unidad.extraer()
    guardar(unidades, ruta(ts, "extract", _prefijo("unidades")))
    guardar(clientes, ruta(ts, "extract", _prefijo("clientes")))
    guardar(condados, ruta(ts, "extract", _prefijo("condados_unidad")))
    guardar(vigentes, ruta(ts, "extract", _prefijo("vigentes")))

    # El rango del calendario sale de los datos, no de una constante: así el
    # modelo no depende de que alguien recuerde ampliarlo cada año.
    rango = query_pinot(
        "SELECT MIN(fechahoraaccidente) AS minimo, MAX(fechahoraaccidente) AS maximo "
        "FROM Fact_Accidente LIMIT 1"
    )
    guardar(rango, ruta(ts, "extract", _prefijo("rango")))


def transform(ts: str, **_) -> None:
    ahora = _ahora()

    def leido(nombre):
        return cargar(ruta(ts, "extract", _prefijo(nombre)))

    rango = leido("rango")
    minimo = a_datetime(rango[0].get("minimo")) if rango else None
    maximo = a_datetime(rango[0].get("maximo")) if rango else None
    desde = (minimo or ahora).date()
    hasta = (maximo or ahora).date()
    guardar(
        dim_tiempo.generar(desde, hasta + timedelta(days=MARGEN_DIAS), ahora),
        ruta(ts, "transform", _prefijo("dim_tiempo")),
    )

    catalogos = {n: leido(n) for n in ("calles", "ciudades", "condados", "estados", "paises")}
    guardar(
        dim_geografia.construir(catalogos, ahora) + [FILAS_DESCONOCIDAS["dim_geografia"](ahora)],
        ruta(ts, "transform", _prefijo("dim_geografia")),
    )
    guardar(
        dim_severidad.construir(leido("severidad"), ahora)
        + [FILAS_DESCONOCIDAS["dim_severidad"](ahora)],
        ruta(ts, "transform", _prefijo("dim_severidad")),
    )
    guardar(
        dim_origen_despacho.construir(leido("origen"), ahora)
        + [FILAS_DESCONOCIDAS["dim_origen_despacho"](ahora)],
        ruta(ts, "transform", _prefijo("dim_origen_despacho")),
    )

    versiones = dim_unidad.construir(
        leido("unidades"), leido("clientes"), leido("condados_unidad"), leido("vigentes"), ahora
    )
    # La fila desconocida solo se escribe si aún no está: es fija, y reescribirla
    # en cada corrida ensuciaría la tabla con versiones idénticas.
    if not leido("vigentes"):
        versiones.append(FILAS_DESCONOCIDAS["dim_unidad"](ahora))
    guardar(versiones, ruta(ts, "transform", _prefijo("dim_unidad")))


def load(ts: str, **_) -> None:
    """Inserta las dimensiones.

    Sin descarte de partición: las dimensiones no están particionadas y el motor
    deduplica por clave. Lo que sí importa es que **una versión cerrada y su
    sustituta se escriben juntas**, para que no exista un instante con dos
    versiones vigentes de la misma unidad.
    """
    for nombre in DIMENSIONES:
        filas = cargar(ruta(ts, "transform", _prefijo(nombre)))
        if filas:
            insert_rows(nombre, ajustar_tipos(nombre, filas))

    # Una dimensión vacía no rompe la carga del hecho —caería en la fila
    # desconocida— pero dejaría **todas** sus columnas desnormalizadas en blanco,
    # que es un fallo silencioso. Mejor detenerse aquí.
    vacias = [
        d for d in DIMENSIONES
        if int(query_clickhouse(f"SELECT count() AS n FROM {d}")[0]["n"]) == 0
    ]
    if vacias:
        raise RuntimeError(f"dimensiones vacías tras la carga: {vacias}")
