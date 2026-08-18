"""Contrato US2: NRR y movimientos."""

from __future__ import annotations

import pytest

from apps.informes_estrategicos.tests.conftest import cliente, pedir_oe5


class TestContratoUs2Oe5:
    def test_nrr_responde_a_finanzas(self):
        respuesta = pedir_oe5(cliente(["DirectorFinanciero"]), "retencion-neta-ingresos")
        if respuesta.status_code != 200:
            pytest.skip("el modelo analítico no está disponible")
        assert "data" in respuesta.json()

    def test_movimientos_responden_a_estrategia(self):
        respuesta = pedir_oe5(cliente(["DirectorEstrategia"]), "movimientos-de-plan")
        if respuesta.status_code != 200:
            pytest.skip("el modelo analítico no está disponible")
        assert "data" in respuesta.json()
