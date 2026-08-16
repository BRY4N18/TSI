"""Tareas del flujo de `hecho_evidencia` (US3).

Quinto hecho del modelo, mismo patrón que los cuatro anteriores.

⚠️ **Depende de `hecho_accidente`, y no solo de las dimensiones.** Copia la
severidad y el condado del caso desde el modelo —no desde el origen—, que es lo
que impide que la copia y su hecho diverjan. Por eso el DAG espera a
`modelo_hecho_accidente` además de a `modelo_dimensiones`: si corriera antes,
todas las evidencias saldrían sin severidad y sin condado, y el informe de
cobertura por severidad quedaría vacío **sin ningún error**.
"""

from __future__ import annotations

from datetime import datetime, timezone

from lib.carga_particion import cargar_particiones
from lib.ddl import ensure_modelo_analitico
from lib.etl_modelo import cargar, guardar, ruta
from lib.hechos import hecho_evidencia
from lib.tipos_almacen import ajustar_tipos

FLUJO = "hecho_evidencia"

FUENTES = ("fotos", "notas", "despachos", "dim_unidad", "hecho_accidente")


def _prefijo(nombre: str) -> str:
    return f"{FLUJO}_{nombre}_"


def _ahora() -> datetime:
    return datetime.now(tz=timezone.utc).replace(tzinfo=None, microsecond=0)


def extract(ts: str, **_) -> None:
    ensure_modelo_analitico()
    datos = hecho_evidencia.extraer()
    for nombre in FUENTES:
        guardar(datos[nombre], ruta(ts, "extract", _prefijo(nombre)))


def transform(ts: str, **_) -> None:
    datos = {n: cargar(ruta(ts, "extract", _prefijo(n))) for n in FUENTES}
    guardar(hecho_evidencia.construir(datos, _ahora()), ruta(ts, "transform", _prefijo("")))


def load(ts: str, **_) -> None:
    filas = ajustar_tipos("hecho_evidencia", cargar(ruta(ts, "transform", _prefijo(""))))
    cargar_particiones("hecho_evidencia", filas)
