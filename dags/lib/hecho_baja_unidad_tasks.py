"""Tareas del flujo de `hecho_baja_unidad` (Red Operativa, US1).

Sexto hecho del modelo, mismo patrón que los cinco anteriores. Que no haya hecho
falta inventar nada aquí es la comprobación de que el patrón escala: el segundo
departamento aporta sus hechos y reutiliza toda la plomería.

⚠️ **Depende de las dimensiones, y la dependencia es real, no formal.** La baja
resuelve `sk_unidad` y `proveedor` por atribución histórica contra `dim_unidad`.
Si corriera antes de que las versiones estén cargadas, todas las bajas caerían en
la unidad desconocida — y el informe de bajas por proveedor saldría entero bajo
«Desconocido», sin ningún error.
"""

from __future__ import annotations

from datetime import datetime, timezone

from lib.carga_particion import cargar_particiones
from lib.ddl import ensure_modelo_analitico
from lib.etl_modelo import cargar, guardar, ruta
from lib.hechos import hecho_baja_unidad
from lib.tipos_almacen import ajustar_tipos

FLUJO = "hecho_baja_unidad"

FUENTES = ("bajas", "dim_unidad")


def _prefijo(nombre: str) -> str:
    return f"{FLUJO}_{nombre}_"


def _ahora() -> datetime:
    return datetime.now(tz=timezone.utc).replace(tzinfo=None, microsecond=0)


def extract(ts: str, **_) -> None:
    ensure_modelo_analitico()
    datos = hecho_baja_unidad.extraer()
    for nombre in FUENTES:
        guardar(datos[nombre], ruta(ts, "extract", _prefijo(nombre)))


def transform(ts: str, **_) -> None:
    datos = {n: cargar(ruta(ts, "extract", _prefijo(n))) for n in FUENTES}
    guardar(hecho_baja_unidad.construir(datos, _ahora()), ruta(ts, "transform", _prefijo("")))


def load(ts: str, **_) -> None:
    filas = ajustar_tipos(FLUJO, cargar(ruta(ts, "transform", _prefijo(""))))
    cargar_particiones(FLUJO, filas)
