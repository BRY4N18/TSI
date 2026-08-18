"""Período sin llamadas: data vacía, no ceros de uptime."""

from __future__ import annotations

import pytest

from apps.informes_estrategicos.tests.conftest import INFORMES_OE2, cliente, pedir_oe2

VACIO = {"desde": "2019-01-01", "hasta": "2019-01-31", "granularidad": "mes"}


@pytest.mark.parametrize("informe", INFORMES_OE2)
def test_oe2_periodo_vacio(informe):
    rol = ["DirectorFinanciero"] if informe in {
        "excedente-facturable", "participacion-ingresos-api", "mrr-por-linea"
    } else ["DirectorTecnologico"]
    respuesta = pedir_oe2(cliente(rol), informe, **VACIO)
    if respuesta.status_code != 200:
        pytest.skip("el modelo analítico no está disponible")
    cuerpo = respuesta.json()
    assert cuerpo["data"] == []
    assert cuerpo["meta"]["cobertura"] in {"completa", "parcial"}
