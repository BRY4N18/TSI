"""Tareas del flujo de `hecho_despacho` (T024).

**Depende del flujo de dimensiones**, y no de forma opcional: la atribución
histórica se resuelve contra `dim_unidad`. Sin sus versiones cargadas, todos los
despachos caerían en la versión desconocida y el hecho quedaría sin proveedor.
"""

from __future__ import annotations

from datetime import datetime, timezone

from lib.carga_particion import cargar_particiones
from lib.ddl import ensure_modelo_analitico
from lib.etl_modelo import cargar, guardar, ruta
from lib.hechos import hecho_despacho
from lib.tipos_almacen import ajustar_tipos

FLUJO = "hecho_despacho"

FUENTES = (
    "despachos",
    "historial",
    "accidentes",
    "dim_unidad",
    "dim_origen",
    "dim_severidad",
    "dim_geografia",
)


def _prefijo(nombre: str) -> str:
    return f"{FLUJO}_{nombre}_"


def _ahora() -> datetime:
    return datetime.now(tz=timezone.utc).replace(tzinfo=None, microsecond=0)


def extract(ts: str, **_) -> None:
    ensure_modelo_analitico()
    datos = hecho_despacho.extraer()
    for nombre in FUENTES:
        guardar(datos[nombre], ruta(ts, "extract", _prefijo(nombre)))


def transform(ts: str, **_) -> None:
    datos = {n: cargar(ruta(ts, "extract", _prefijo(n))) for n in FUENTES}
    guardar(hecho_despacho.construir(datos, _ahora()), ruta(ts, "transform", _prefijo("")))


def load(ts: str, **_) -> None:
    filas = ajustar_tipos("hecho_despacho", cargar(ruta(ts, "transform", _prefijo(""))))
    cargar_particiones("hecho_despacho", filas)
