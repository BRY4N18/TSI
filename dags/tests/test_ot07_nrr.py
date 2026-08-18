"""T055 — el NRR excluye a los clientes nuevos."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.almacen import (  # noqa: E402
    ID_SUSCRIPCION_PRUEBA,
    asegurar_hechos_suscripciones,
    ejecutar_suscripciones,
    insertar,
    limpiar_suscripciones,
    requiere_modelo,
    suscripcion_de_prueba,
)


@pytest.fixture
def escenario():
    asegurar_hechos_suscripciones()
    limpiar_suscripciones()
    insertar("hecho_suscripcion", [
        suscripcion_de_prueba(
            ID_SUSCRIPCION_PRUEBA,
            idcliente=990010,
            precio_mensualizado=100.0,
            fecha_alta="2099-11-01 08:00:00",
        ),
        suscripcion_de_prueba(
            ID_SUSCRIPCION_PRUEBA + 1,
            idcliente=990011,
            precio_mensualizado=50.0,
            fecha_alta="2099-12-01 08:00:00",
        ),
        suscripcion_de_prueba(
            ID_SUSCRIPCION_PRUEBA + 2,
            idcliente=990012,
            estado_derivado="cancelada",
            precio_mensualizado=40.0,
            fecha_alta="2099-10-01 08:00:00",
            fecha_cancelacion="2099-12-10 08:00:00",
        ),
    ])
    yield
    limpiar_suscripciones()


@requiere_modelo
class TestNrr:
    def test_excluye_nuevos_y_explica_la_cifra(self, escenario):
        filas = ejecutar_suscripciones("ot07_nrr")
        assert filas
        fila = filas[0]
        assert float(fila["mrr_inicial"]) == pytest.approx(140.0)
        assert float(fila["baja"]) == pytest.approx(40.0)
        restante = float(fila["mrr_inicial"]) - float(fila["baja"]) + float(fila["expansion"]) - float(fila["contraccion"])
        assert restante == pytest.approx(100.0)
        assert float(fila["nrr"]) == pytest.approx(restante / float(fila["mrr_inicial"]), abs=0.01)
