"""T052, T053 — pendiente fuera de la mediana; rechazada cuenta como resuelta."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.almacen import (  # noqa: E402
    asegurar_hechos_suscripciones,
    ejecutar_suscripciones,
    insertar,
    limpiar_suscripciones,
    requiere_modelo,
    solicitud_de_prueba,
)


@pytest.fixture
def escenario():
    asegurar_hechos_suscripciones()
    limpiar_suscripciones()
    insertar("hecho_solicitud_cambio_plan", [
        solicitud_de_prueba(990001, estado="aprobada", segundos_resolucion=5000),
        solicitud_de_prueba(990002, estado="rechazada", segundos_resolucion=7000),
        solicitud_de_prueba(990003, estado="pendiente", segundos_resolucion=None),
    ])
    yield
    limpiar_suscripciones()


@requiere_modelo
class TestTiempoResolucion:
    def test_la_pendiente_queda_fuera_de_la_mediana(self, escenario):
        filas = ejecutar_suscripciones("ot07_tiempo_resolucion")
        assert filas
        fila = filas[0]
        assert int(fila["pendientes"]) == 1
        assert int(fila["resueltas"]) == 2
        mediana = float(fila["segundos_mediana"])
        assert mediana in (5000.0, 6000.0, 7000.0)
        assert mediana != 0

    def test_la_rechazada_cuenta_como_resuelta(self, escenario):
        fila = ejecutar_suscripciones("ot07_tiempo_resolucion")[0]
        assert int(fila["resueltas"]) == 2
