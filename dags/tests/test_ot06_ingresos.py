"""T039 — las notas de crédito restan solas (SC-006)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.almacen import (  # noqa: E402
    asegurar_hechos_suscripciones,
    ejecutar_suscripciones,
    factura_de_prueba,
    insertar,
    limpiar_suscripciones,
    requiere_modelo,
)


@pytest.fixture
def escenario():
    asegurar_hechos_suscripciones()
    limpiar_suscripciones()
    insertar("hecho_factura", [
        factura_de_prueba("fac-1", monto_total=100.0, es_nota_credito=0),
        factura_de_prueba("fac-2", monto_total=30.0, es_nota_credito=1, estado_pago="Pagada"),
    ])
    yield
    limpiar_suscripciones()


@requiere_modelo
class TestNotasDeCredito:
    def test_el_ingreso_neto_es_menor_que_sumar_sin_signo(self, escenario):
        filas = ejecutar_suscripciones("ot06_ingresos")
        assert filas
        neto = sum(float(f["ingreso_neto"]) for f in filas)
        bruto = sum(float(f["facturado"]) for f in filas)
        notas = sum(float(f["notas_credito"]) for f in filas)
        assert neto == pytest.approx(70.0)
        assert bruto == pytest.approx(100.0)
        assert notas == pytest.approx(30.0)
        assert neto < bruto
