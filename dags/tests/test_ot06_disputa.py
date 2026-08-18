"""T040 — una factura en disputa no es impago ni suma mora (SC-005)."""

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
        factura_de_prueba(
            "fac-disputa",
            monto_total=80.0,
            estado_pago="En disputa",
            pagada_primer_intento=0,
            dias_mora=None,
        ),
        factura_de_prueba(
            "fac-mora",
            monto_total=50.0,
            estado_pago="Pendiente",
            pagada_primer_intento=0,
            dias_mora=4,
        ),
    ])
    yield
    limpiar_suscripciones()


@requiere_modelo
class TestDisputaNoEsImpago:
    def test_no_aparece_entre_pagadas_ni_en_dunning_como_impago(self, escenario):
        cobro = ejecutar_suscripciones("ot06_cobro_primer_intento")
        for fila in cobro:
            assert int(fila["pagadas"]) == 0
        dunning = ejecutar_suscripciones("ot06_efectividad_dunning")
        ids_estado = {str(f) for f in dunning}
        assert "En disputa" not in str(ids_estado)
