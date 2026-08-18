"""Tareas del flujo conjunto de nutricion del prospecto (Ventas y CRM, US3).

Demo y notificacion se cargan juntas. La latencia de reaccion se deriva en la
carga cruzando el aviso con el primer avance de etapa posterior; si los dos
hechos corrieran en DAGs distintos, habria ventanas en las que los avisos
existirian sin su reaccion calculada, y el informe de latencia contaria como
ignorados avisos que ya se atendieron.
"""

from __future__ import annotations

from datetime import datetime, timezone

from lib.carga_particion import cargar_particiones
from lib.ddl import ensure_modelo_analitico
from lib.etl_modelo import cargar, guardar, ruta
from lib.hechos import hecho_interaccion_demo, hecho_notificacion_ventas
from lib.tipos_almacen import ajustar_tipos

FLUJO = "hecho_nutricion"

FUENTES = ("interacciones", "notificaciones", "transiciones", "dim_prospecto")


def _prefijo(nombre: str) -> str:
    return f"{FLUJO}_{nombre}_"


def _ahora() -> datetime:
    return datetime.now(tz=timezone.utc).replace(tzinfo=None, microsecond=0)


def extract(ts: str, **_) -> None:
    ensure_modelo_analitico()
    demos = hecho_interaccion_demo.extraer()
    avisos = hecho_notificacion_ventas.extraer()
    guardar(demos["interacciones"], ruta(ts, "extract", _prefijo("interacciones")))
    guardar(avisos["notificaciones"], ruta(ts, "extract", _prefijo("notificaciones")))
    guardar(avisos["transiciones"], ruta(ts, "extract", _prefijo("transiciones")))
    guardar(avisos["dim_prospecto"], ruta(ts, "extract", _prefijo("dim_prospecto")))


def transform(ts: str, **_) -> None:
    datos = {n: cargar(ruta(ts, "extract", _prefijo(n))) for n in FUENTES}
    ahora = _ahora()
    guardar(
        hecho_interaccion_demo.construir(
            {"interacciones": datos["interacciones"], "dim_prospecto": datos["dim_prospecto"]},
            ahora,
        ),
        ruta(ts, "transform", _prefijo("demo")),
    )
    guardar(
        hecho_notificacion_ventas.construir(
            {
                "notificaciones": datos["notificaciones"],
                "transiciones": datos["transiciones"],
                "dim_prospecto": datos["dim_prospecto"],
            },
            ahora,
        ),
        ruta(ts, "transform", _prefijo("aviso")),
    )


def load(ts: str, **_) -> None:
    demos = ajustar_tipos(
        "hecho_interaccion_demo",
        cargar(ruta(ts, "transform", _prefijo("demo"))),
    )
    avisos = ajustar_tipos(
        "hecho_notificacion_ventas",
        cargar(ruta(ts, "transform", _prefijo("aviso"))),
    )
    cargar_particiones("hecho_interaccion_demo", demos)
    cargar_particiones("hecho_notificacion_ventas", avisos)
