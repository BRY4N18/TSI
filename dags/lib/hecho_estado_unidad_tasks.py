"""Tareas del flujo de `hecho_estado_unidad` (T040).

**Es la prueba real del crecimiento**: este fichero es idéntico en estructura a
los otros dos flujos de hechos. Añadir un hecho no exigió inventar nada nuevo —
mismas piezas, mismo patrón, misma carga por partición.
"""

from __future__ import annotations

from datetime import datetime, timezone

from lib.carga_particion import cargar_particiones
from lib.ddl import ensure_modelo_analitico
from lib.etl_modelo import cargar, guardar, ruta
from lib.hechos import hecho_estado_unidad
from lib.tipos_almacen import ajustar_tipos

FLUJO = "hecho_estado_unidad"

FUENTES = ("historial", "dim_unidad")


def _prefijo(nombre: str) -> str:
    return f"{FLUJO}_{nombre}_"


def _ahora() -> datetime:
    return datetime.now(tz=timezone.utc).replace(tzinfo=None, microsecond=0)


def extract(ts: str, **_) -> None:
    ensure_modelo_analitico()
    datos = hecho_estado_unidad.extraer()
    for nombre in FUENTES:
        guardar(datos[nombre], ruta(ts, "extract", _prefijo(nombre)))


def transform(ts: str, **_) -> None:
    datos = {n: cargar(ruta(ts, "extract", _prefijo(n))) for n in FUENTES}
    guardar(hecho_estado_unidad.construir(datos, _ahora()), ruta(ts, "transform", _prefijo("")))


def load(ts: str, **_) -> None:
    filas = ajustar_tipos("hecho_estado_unidad", cargar(ruta(ts, "transform", _prefijo(""))))
    cargar_particiones("hecho_estado_unidad", filas)
