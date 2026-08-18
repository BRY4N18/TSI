"""Contrato US1: cuatro informes de consumo. Skip si el almacén no está."""

from __future__ import annotations

import json

import pytest

from apps.informes_estrategicos.tests.conftest import (
    BASE_OE2,
    PERIODO,
    SENSIBLES,
    cliente,
    pedir_oe2,
)

US1 = (
    "integraciones-activas",
    "consumo-por-partner",
    "latencia-por-endpoint",
    "taxonomia-errores",
)


@pytest.fixture
def tecnologico():
    return cliente(["DirectorTecnologico"])


class TestContratoUs1Oe2:
    def test_los_cuatro_responden(self, tecnologico):
        for informe in US1:
            respuesta = pedir_oe2(tecnologico, informe)
            if respuesta.status_code != 200:
                pytest.skip("el modelo analítico no está disponible")
            cuerpo = respuesta.json()
            assert set(cuerpo) == {"data", "meta"}
            assert "acotado_a" not in cuerpo["meta"]

    def test_falta_granularidad_es_400(self, tecnologico):
        respuesta = tecnologico.get(
            f"{BASE_OE2}/integraciones-activas",
            {"desde": PERIODO["desde"], "hasta": PERIODO["hasta"]},
        )
        assert respuesta.status_code == 400
        assert "granularidad" in str(respuesta.json()).lower()

    @pytest.mark.parametrize("informe", US1)
    def test_sin_secretos(self, tecnologico, informe):
        respuesta = pedir_oe2(tecnologico, informe)
        if respuesta.status_code != 200:
            pytest.skip("el modelo analítico no está disponible")
        texto = json.dumps(respuesta.json()).lower()
        for sensible in SENSIBLES + ("client_secret",):
            assert sensible not in texto, f"{informe} expone {sensible}"
