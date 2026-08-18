"""T063 — un plan de precio cero cuenta en clientes y aporta cero ingreso."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.almacen import (  # noqa: E402
    ID_PLAN_PRUEBA,
    ID_SUSCRIPCION_PRUEBA,
    asegurar_hechos_suscripciones,
    ejecutar_suscripciones,
    insertar,
    limpiar_suscripciones,
    plan_de_prueba,
    requiere_modelo,
    suscripcion_de_prueba,
)


@pytest.fixture
def escenario():
    asegurar_hechos_suscripciones()
    limpiar_suscripciones()
    insertar("dim_plan", [
        plan_de_prueba(ID_PLAN_PRUEBA, nombre="Demo", precio_lista=0),
        plan_de_prueba(ID_PLAN_PRUEBA + 1, nombre="Pago", precio_lista=100),
    ])
    insertar("hecho_suscripcion", [
        suscripcion_de_prueba(
            ID_SUSCRIPCION_PRUEBA,
            plan="Demo",
            idplan=ID_PLAN_PRUEBA,
            precio=0,
            precio_mensualizado=0,
        ),
        suscripcion_de_prueba(
            ID_SUSCRIPCION_PRUEBA + 1,
            idcliente=990001,
            plan="Pago",
            idplan=ID_PLAN_PRUEBA + 1,
            precio=100,
            precio_mensualizado=100,
        ),
    ])
    yield
    limpiar_suscripciones()


@requiere_modelo
class TestDistribucion:
    def test_el_plan_cero_no_desaparece(self, escenario):
        filas = ejecutar_suscripciones("ot05_distribucion_cartera")
        por_plan = {f["plan"]: f for f in filas}
        assert "Demo" in por_plan
        assert int(por_plan["Demo"]["clientes"]) == 1
        assert float(por_plan["Demo"]["mrr_aportado"]) == pytest.approx(0.0)
        assert float(por_plan["Pago"]["mrr_aportado"]) == pytest.approx(100.0)
