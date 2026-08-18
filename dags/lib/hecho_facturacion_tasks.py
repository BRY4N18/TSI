"""Tareas del flujo conjunto de facturación (factura + solicitud de cambio).

Se cargan juntos porque comparten fuente y ciclo: un cambio de plan genera
factura, y cargarlos por separado dejaría ventanas en las que el ingreso ya
está y el movimiento no, o al revés.
"""

from __future__ import annotations

from datetime import datetime, timezone

from lib.carga_particion import cargar_particiones
from lib.ddl import ensure_modelo_analitico
from lib.etl_modelo import cargar, guardar, ruta
from lib.hechos import hecho_factura, hecho_solicitud_cambio_plan
from lib.tipos_almacen import ajustar_tipos

FLUJO = "hecho_facturacion"

FUENTES_FACTURA = ("facturas", "hecho_suscripcion", "dim_cliente")
FUENTES_SOLICITUD = ("solicitudes", "dim_plan")


def _prefijo(nombre: str) -> str:
    return f"{FLUJO}_{nombre}_"


def _ahora() -> datetime:
    return datetime.now(tz=timezone.utc).replace(tzinfo=None, microsecond=0)


def extract(ts: str, **_) -> None:
    ensure_modelo_analitico()
    facturas = hecho_factura.extraer()
    solicitudes = hecho_solicitud_cambio_plan.extraer()
    for nombre in FUENTES_FACTURA:
        guardar(facturas[nombre], ruta(ts, "extract", _prefijo(nombre)))
    for nombre in FUENTES_SOLICITUD:
        guardar(solicitudes[nombre], ruta(ts, "extract", _prefijo(nombre)))


def transform(ts: str, **_) -> None:
    ahora = _ahora()
    datos_f = {n: cargar(ruta(ts, "extract", _prefijo(n))) for n in FUENTES_FACTURA}
    datos_s = {n: cargar(ruta(ts, "extract", _prefijo(n))) for n in FUENTES_SOLICITUD}
    guardar(hecho_factura.construir(datos_f, ahora), ruta(ts, "transform", _prefijo("factura")))
    guardar(
        hecho_solicitud_cambio_plan.construir(datos_s, ahora),
        ruta(ts, "transform", _prefijo("solicitud")),
    )


def load(ts: str, **_) -> None:
    facturas = ajustar_tipos(
        "hecho_factura", cargar(ruta(ts, "transform", _prefijo("factura")))
    )
    solicitudes = ajustar_tipos(
        "hecho_solicitud_cambio_plan",
        cargar(ruta(ts, "transform", _prefijo("solicitud"))),
    )
    cargar_particiones("hecho_factura", facturas)
    cargar_particiones("hecho_solicitud_cambio_plan", solicitudes)
