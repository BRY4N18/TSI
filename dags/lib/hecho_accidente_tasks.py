"""Tareas del flujo de `hecho_accidente` (T024).

Carga idempotente por partición: recargar un período deja **el mismo número
exacto de filas**, porque la partición se descarta antes de insertar.
"""

from __future__ import annotations

from datetime import datetime, timezone

from lib.carga_particion import cargar_particiones
from lib.ddl import ensure_modelo_analitico
from lib.etl_modelo import cargar, guardar, ruta
from lib.hechos import hecho_accidente
from lib.tipos_almacen import ajustar_tipos

FLUJO = "hecho_accidente"

#: Fuentes que `extraer()` devuelve y que `transform` vuelve a cargar.
#:
#: Anadir una fuente al modulo de logica y olvidarla aqui **no falla**: el
#: `datos.get(nombre, [])` de `construir` la sustituye por una lista vacia, y
#: todos los recuentos de esa fuente salen a CERO. Como cero es un valor
#: legitimo en esas columnas -cero notas es una medicion-, el resultado es
#: indistinguible de un origen sin datos. Paso exactamente eso al implementar las
#: metricas de la US3, y solo se vio comparando con el origen.
#:
#: La prueba `test_hecho_accidente_fuentes` comprueba que esta tupla y las claves
#: de `extraer()` son la misma cosa.
FUENTES = (
    "accidentes",
    "estados",
    "despachos",
    "tipos",
    "evidencia",
    "notas",
    "conductores",
    "implicados",
    "clima",
    "historial_severidad",
    "cierres",
    "dim_severidad",
    "dim_geografia",
)


def _prefijo(nombre: str) -> str:
    return f"{FLUJO}_{nombre}_"


def _ahora() -> datetime:
    return datetime.now(tz=timezone.utc).replace(tzinfo=None, microsecond=0)


def extract(ts: str, **_) -> None:
    ensure_modelo_analitico()
    datos = hecho_accidente.extraer()
    for nombre in FUENTES:
        guardar(datos[nombre], ruta(ts, "extract", _prefijo(nombre)))


def transform(ts: str, **_) -> None:
    datos = {n: cargar(ruta(ts, "extract", _prefijo(n))) for n in FUENTES}
    guardar(hecho_accidente.construir(datos, _ahora()), ruta(ts, "transform", _prefijo("")))


def load(ts: str, **_) -> None:
    filas = ajustar_tipos("hecho_accidente", cargar(ruta(ts, "transform", _prefijo(""))))
    cargar_particiones("hecho_accidente", filas)
