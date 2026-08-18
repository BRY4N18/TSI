"""T041 — el cliente sin ninguna fila de método sí aparece."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.almacen import (  # noqa: E402
    ID_CLIENTE_PRUEBA,
    asegurar_hechos_suscripciones,
    cliente_de_prueba,
    ejecutar_suscripciones,
    insertar,
    limpiar_suscripciones,
    requiere_modelo,
)


@pytest.fixture
def escenario():
    asegurar_hechos_suscripciones()
    limpiar_suscripciones()
    insertar("dim_cliente", [
        cliente_de_prueba(ID_CLIENTE_PRUEBA, nombre="Sin método", tiene_metodo_pago=0),
        cliente_de_prueba(ID_CLIENTE_PRUEBA + 1, nombre="Con método", tiene_metodo_pago=1),
    ])
    yield
    limpiar_suscripciones()


@requiere_modelo
class TestSinMetodo:
    def test_aparece_quien_no_tiene_fila(self, escenario):
        filas = ejecutar_suscripciones("ot06_clientes_sin_metodo_pago")
        ids = {int(f["idcliente"]) for f in filas}
        assert ID_CLIENTE_PRUEBA in ids
        assert ID_CLIENTE_PRUEBA + 1 not in ids
