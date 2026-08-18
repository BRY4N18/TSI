"""Tareas del flujo de soporte: los dos hechos en un solo DAG.

Comparten fuente —el ciclo del ticket— y su cadencia es la misma. Separarlos
multiplicaría la plomería sin ganar nada.
"""

from __future__ import annotations

from datetime import datetime, timezone

from lib.carga_particion import cargar_particiones
from lib.ddl import ensure_modelo_analitico
from lib.etl_modelo import cargar, guardar, ruta
from lib.hechos import hecho_accion_ticket, hecho_ticket
from lib.tipos_almacen import ajustar_tipos

FLUJO = "hecho_soporte"

FUENTES_TICKET = (
    "tickets", "historial", "suscripciones",
    "dim_sla_config", "dim_plan", "dim_servicio", "dim_cliente",
)
FUENTES_ACCION = ("historial", "tickets")


def _prefijo(nombre: str) -> str:
    return f"{FLUJO}_{nombre}_"


def _ahora() -> datetime:
    return datetime.now(tz=timezone.utc).replace(tzinfo=None, microsecond=0)


def extract(ts: str, **_) -> None:
    ensure_modelo_analitico()
    datos = hecho_ticket.extraer()
    for nombre in FUENTES_TICKET:
        guardar(datos[nombre], ruta(ts, "extract", _prefijo(nombre)))


def transform(ts: str, **_) -> None:
    ahora = _ahora()
    datos_ticket = {n: cargar(ruta(ts, "extract", _prefijo(n))) for n in FUENTES_TICKET}
    guardar(hecho_ticket.construir(datos_ticket, ahora), ruta(ts, "transform", _prefijo("ticket")))
    datos_accion = {n: cargar(ruta(ts, "extract", _prefijo(n))) for n in FUENTES_ACCION}
    guardar(
        hecho_accion_ticket.construir(datos_accion, ahora),
        ruta(ts, "transform", _prefijo("accion")),
    )


def load(ts: str, **_) -> None:
    tickets = ajustar_tipos("hecho_ticket", cargar(ruta(ts, "transform", _prefijo("ticket"))))
    acciones = ajustar_tipos(
        "hecho_accion_ticket", cargar(ruta(ts, "transform", _prefijo("accion")))
    )
    cargar_particiones("hecho_ticket", tickets)
    cargar_particiones("hecho_accion_ticket", acciones)
