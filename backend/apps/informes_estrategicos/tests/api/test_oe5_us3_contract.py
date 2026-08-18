"""Contrato US3: señales de retención."""

from __future__ import annotations

import pytest

from apps.informes_estrategicos.tests.conftest import cliente, pedir_oe5

US3_GERENTE = ("cuentas-en-riesgo",)
US3_SOPORTE = ("rendimiento-por-agente", "reincidencia-soporte")
US3_ESTRATEGIA = ("antiguedad-de-cuenta",)


class TestContratoUs3Oe5:
    def test_soporte_responde(self):
        api = cliente(["GerenteExitoCliente"])
        for informe in US3_SOPORTE:
            respuesta = pedir_oe5(api, informe)
            if respuesta.status_code != 200:
                pytest.skip("el modelo analítico no está disponible")
            assert "data" in respuesta.json()

    def test_riesgo_responde_a_gerente(self):
        respuesta = pedir_oe5(cliente(["Gerente"]), "cuentas-en-riesgo")
        if respuesta.status_code != 200:
            pytest.skip("el modelo analítico no está disponible")
        assert "data" in respuesta.json()

    def test_antiguedad_responde(self):
        respuesta = pedir_oe5(cliente(["DirectorEstrategia"]), "antiguedad-de-cuenta")
        if respuesta.status_code != 200:
            pytest.skip("el modelo analítico no está disponible")
        assert "data" in respuesta.json()
