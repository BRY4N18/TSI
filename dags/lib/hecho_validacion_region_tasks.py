"""Tareas del flujo de `hecho_validacion_region` (Red Operativa, US2).

Septimo hecho del modelo, mismo patron. ⚠️ Depende de `dim_region`: resuelve la
version de region vigente **al validar**. Sin ella cargada, todas las
validaciones caerian en la region desconocida y el informe por region saldria
vacio sin que nada fallara.
"""

from __future__ import annotations

from datetime import datetime, timezone

from lib.carga_particion import cargar_particiones
from lib.ddl import ensure_modelo_analitico
from lib.etl_modelo import cargar, guardar, ruta
from lib.hechos import hecho_validacion_region
from lib.tipos_almacen import ajustar_tipos

FLUJO = "hecho_validacion_region"

FUENTES = ("validaciones", "dim_region")


def _prefijo(nombre: str) -> str:
    return f"{FLUJO}_{nombre}_"


def _ahora() -> datetime:
    return datetime.now(tz=timezone.utc).replace(tzinfo=None, microsecond=0)


def extract(ts: str, **_) -> None:
    ensure_modelo_analitico()
    datos = hecho_validacion_region.extraer()
    for nombre in FUENTES:
        guardar(datos[nombre], ruta(ts, "extract", _prefijo(nombre)))


def transform(ts: str, **_) -> None:
    datos = {n: cargar(ruta(ts, "extract", _prefijo(n))) for n in FUENTES}
    guardar(
        hecho_validacion_region.construir(datos, _ahora()),
        ruta(ts, "transform", _prefijo("")),
    )


def load(ts: str, **_) -> None:
    filas = ajustar_tipos(FLUJO, cargar(ruta(ts, "transform", _prefijo(""))))
    cargar_particiones(FLUJO, filas)
