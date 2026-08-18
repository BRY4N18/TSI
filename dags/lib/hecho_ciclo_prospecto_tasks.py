"""Tareas del flujo conjunto del ciclo del prospecto (Ventas y CRM, US1).

Los dos hechos —transicion de embudo y asignacion— **comparten fuente y se
cargan juntos**. No son dos DAGs: un prospecto que cambia de etapa y de
ejecutivo el mismo dia es un solo ciclo, y cargarlos por separado dejaria
ventanas en las que el embudo ya esta actualizado y la cartera no, o al reves.

⚠️ Depende de `dim_prospecto`. Sin ella, empresa y canal caerian en
«Desconocido» y el informe de carga por canal saldria entero bajo esa etiqueta
sin que nada fallara.
"""

from __future__ import annotations

from datetime import datetime, timezone

from lib.carga_particion import cargar_particiones
from lib.ddl import ensure_modelo_analitico
from lib.etl_modelo import cargar, guardar, ruta
from lib.hechos import hecho_asignacion_prospecto, hecho_transicion_embudo
from lib.tipos_almacen import ajustar_tipos

FLUJO = "hecho_ciclo_prospecto"

FUENTES = ("transiciones", "asignaciones", "dim_prospecto")


def _prefijo(nombre: str) -> str:
    return f"{FLUJO}_{nombre}_"


def _ahora() -> datetime:
    return datetime.now(tz=timezone.utc).replace(tzinfo=None, microsecond=0)


def extract(ts: str, **_) -> None:
    ensure_modelo_analitico()
    transiciones = hecho_transicion_embudo.extraer()
    asignaciones = hecho_asignacion_prospecto.extraer()
    guardar(transiciones["transiciones"], ruta(ts, "extract", _prefijo("transiciones")))
    guardar(asignaciones["asignaciones"], ruta(ts, "extract", _prefijo("asignaciones")))
    guardar(transiciones["dim_prospecto"], ruta(ts, "extract", _prefijo("dim_prospecto")))


def transform(ts: str, **_) -> None:
    datos = {n: cargar(ruta(ts, "extract", _prefijo(n))) for n in FUENTES}
    ahora = _ahora()
    guardar(
        hecho_transicion_embudo.construir(
            {"transiciones": datos["transiciones"], "dim_prospecto": datos["dim_prospecto"]},
            ahora,
        ),
        ruta(ts, "transform", _prefijo("transicion")),
    )
    guardar(
        hecho_asignacion_prospecto.construir(
            {"asignaciones": datos["asignaciones"], "dim_prospecto": datos["dim_prospecto"]},
            ahora,
        ),
        ruta(ts, "transform", _prefijo("asignacion")),
    )


def load(ts: str, **_) -> None:
    transiciones = ajustar_tipos(
        "hecho_transicion_embudo",
        cargar(ruta(ts, "transform", _prefijo("transicion"))),
    )
    asignaciones = ajustar_tipos(
        "hecho_asignacion_prospecto",
        cargar(ruta(ts, "transform", _prefijo("asignacion"))),
    )
    cargar_particiones("hecho_transicion_embudo", transiciones)
    cargar_particiones("hecho_asignacion_prospecto", asignaciones)
