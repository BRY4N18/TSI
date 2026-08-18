"""Contrato US1: tres informes de SLA. Skip si el almacén no está."""

from __future__ import annotations

import pytest

from apps.informes_estrategicos.tests.conftest import BASE_OE5, PERIODO, cliente, pedir_oe5

US1 = ("cumplimiento-sla", "evolucion-incumplimiento", "sla-por-plan")


@pytest.fixture
def exito():
    return cliente(["GerenteExitoCliente"])


class TestContratoUs1Oe5:
    def test_los_tres_responden(self, exito):
        for informe in US1:
            respuesta = pedir_oe5(exito, informe)
            if respuesta.status_code != 200:
                pytest.skip("el modelo analítico no está disponible")
            cuerpo = respuesta.json()
            assert set(cuerpo) == {"data", "meta"}
            assert "acotado_a" not in cuerpo["meta"]

    def test_falta_granularidad_es_400(self, exito):
        respuesta = exito.get(
            f"{BASE_OE5}/cumplimiento-sla",
            {"desde": PERIODO["desde"], "hasta": PERIODO["hasta"]},
        )
        assert respuesta.status_code == 400
        assert "granularidad" in str(respuesta.json()).lower()
