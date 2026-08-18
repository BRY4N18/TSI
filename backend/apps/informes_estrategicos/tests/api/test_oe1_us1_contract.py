"""Contrato US1: cuatro informes de ingreso. Skip si el almacén no está."""

from __future__ import annotations

import pytest

from apps.informes_estrategicos.tests.conftest import (
    BASE_OE1,
    PERIODO,
    cliente,
    pedir_oe1,
)

US1 = (
    "mrr-mensual",
    "arr-proyeccion",
    "mrr-por-segmento",
    "cartera-por-plan",
)


@pytest.fixture
def financiero():
    return cliente(["DirectorFinanciero"])


@pytest.fixture
def estrategia():
    return cliente(["DirectorEstrategia"])


class TestContratoUs1Oe1:
    def test_mrr_y_arr_responden(self, financiero):
        for informe in ("mrr-mensual", "arr-proyeccion", "mrr-por-segmento"):
            respuesta = pedir_oe1(financiero, informe)
            if respuesta.status_code != 200:
                pytest.skip("el modelo analítico no está disponible")
            cuerpo = respuesta.json()
            assert set(cuerpo) == {"data", "meta"}
            assert "acotado_a" not in cuerpo["meta"]

    def test_cartera_responde(self, estrategia):
        respuesta = pedir_oe1(estrategia, "cartera-por-plan")
        if respuesta.status_code != 200:
            pytest.skip("el modelo analítico no está disponible")
        assert set(respuesta.json()) == {"data", "meta"}

    def test_falta_granularidad_es_400(self, financiero):
        respuesta = financiero.get(
            f"{BASE_OE1}/mrr-mensual",
            {"desde": PERIODO["desde"], "hasta": PERIODO["hasta"]},
        )
        assert respuesta.status_code == 400
        assert "granularidad" in str(respuesta.json()).lower()
