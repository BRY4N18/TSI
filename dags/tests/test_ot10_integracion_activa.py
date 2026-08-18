"""T059 — el denominador son todos los clientes (SC-007)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.almacen import (  # noqa: E402
    ID_CLIENTE_PRUEBA,
    ID_PARTNER_PRUEBA,
    asegurar_hechos_partners,
    cliente_de_prueba,
    ejecutar_partners,
    insertar,
    limpiar_partners,
    partner_de_prueba,
    requiere_modelo,
)


@pytest.fixture
def escenario():
    asegurar_hechos_partners()
    limpiar_partners()
    insertar("dim_cliente", [
        cliente_de_prueba(ID_CLIENTE_PRUEBA),
        cliente_de_prueba(ID_CLIENTE_PRUEBA + 1, nombre="Sin partner"),
    ])
    insertar("dim_partner", [
        partner_de_prueba(ID_PARTNER_PRUEBA, idcliente=ID_CLIENTE_PRUEBA),
    ])
    yield
    limpiar_partners()


@requiere_modelo
def test_el_porcentaje_es_menor_que_cien(escenario):
    filas = ejecutar_partners("ot10_clientes_integracion_activa")
    assert filas
    fila = filas[0]
    assert int(fila["clientes_totales"]) >= 2
    assert int(fila["con_integracion"]) >= 1
    assert float(fila["pct"]) < 1.0
    assert float(fila["meta"]) == pytest.approx(0.70)
