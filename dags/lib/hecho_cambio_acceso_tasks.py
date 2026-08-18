"""Tareas del flujo de `hecho_cambio_acceso`."""

from __future__ import annotations

from datetime import datetime, timezone

from lib.carga_particion import cargar_particiones
from lib.ddl import ensure_modelo_analitico
from lib.etl_modelo import cargar, guardar, ruta
from lib.hechos import hecho_cambio_acceso
from lib.tipos_almacen import ajustar_tipos

FLUJO = "hecho_cambio_acceso"
FUENTES = ("bitacora", "partners")


def _prefijo(nombre: str) -> str:
    return f"{FLUJO}_{nombre}_"


def _ahora() -> datetime:
    return datetime.now(tz=timezone.utc).replace(tzinfo=None, microsecond=0)


def extract(ts: str, **_) -> None:
    ensure_modelo_analitico()
    datos = hecho_cambio_acceso.extraer()
    for nombre in FUENTES:
        guardar(datos[nombre], ruta(ts, "extract", _prefijo(nombre)))


def transform(ts: str, **_) -> None:
    datos = {n: cargar(ruta(ts, "extract", _prefijo(n))) for n in FUENTES}
    guardar(hecho_cambio_acceso.construir(datos, _ahora()), ruta(ts, "transform", _prefijo("")))


def load(ts: str, **_) -> None:
    filas = ajustar_tipos("hecho_cambio_acceso", cargar(ruta(ts, "transform", _prefijo(""))))
    cargar_particiones("hecho_cambio_acceso", filas)
