"""Tareas del flujo de `hecho_ping_unidad` (fase 6).

Cuarto hecho, mismo patrón que los otros tres. Es el más voluminoso del modelo,
así que es también la primera prueba de que la carga por partición escala más
allá de unos miles de filas.
"""

from __future__ import annotations

from datetime import datetime, timezone

from lib.carga_particion import cargar_particiones
from lib.ddl import ensure_modelo_analitico
from lib.etl_modelo import cargar, guardar, ruta
from lib.hechos import hecho_ping_unidad
from lib.tipos_almacen import ajustar_tipos

FLUJO = "hecho_ping_unidad"

FUENTES = ("pings", "dim_unidad")


def _prefijo(nombre: str) -> str:
    return f"{FLUJO}_{nombre}_"


def _ahora() -> datetime:
    return datetime.now(tz=timezone.utc).replace(tzinfo=None, microsecond=0)


def extract(ts: str, **_) -> None:
    ensure_modelo_analitico()
    datos = hecho_ping_unidad.extraer()
    for nombre in FUENTES:
        guardar(datos[nombre], ruta(ts, "extract", _prefijo(nombre)))


def transform(ts: str, **_) -> None:
    datos = {n: cargar(ruta(ts, "extract", _prefijo(n))) for n in FUENTES}
    guardar(hecho_ping_unidad.construir(datos, _ahora()), ruta(ts, "transform", _prefijo("")))


def load(ts: str, **_) -> None:
    filas = ajustar_tipos("hecho_ping_unidad", cargar(ruta(ts, "transform", _prefijo(""))))
    cargar_particiones("hecho_ping_unidad", filas)
