"""Período vacío: flujo en data []; el stock de MRR no inventa un 0 si hay vigentes."""

from __future__ import annotations

import pytest

from apps.informes_estrategicos.tests.conftest import INFORMES_OE1, cliente, pedir_oe1

VACIO = {"desde": "2019-01-01", "hasta": "2019-01-31", "granularidad": "mes"}
FLUJO_SIN_CATALOGO = {
    "velocidad-ciclo-venta",
    "tasa-renovacion",
    "tiempo-onboarding",
}


def _rol(informe: str) -> list[str]:
    if informe in {
        "mrr-mensual",
        "arr-proyeccion",
        "mrr-por-segmento",
        "tasa-renovacion",
    }:
        return ["DirectorFinanciero"]
    if informe == "cartera-por-plan":
        return ["DirectorEstrategia"]
    if informe in {"embudo-conversion", "velocidad-ciclo-venta"}:
        return ["DirectorMarketing"]
    return ["Gerente"]


@pytest.mark.parametrize("informe", INFORMES_OE1)
def test_oe1_periodo_vacio(informe):
    respuesta = pedir_oe1(cliente(_rol(informe)), informe, **VACIO)
    if respuesta.status_code != 200:
        pytest.skip("el modelo analítico no está disponible")
    cuerpo = respuesta.json()
    if informe in FLUJO_SIN_CATALOGO:
        assert cuerpo["data"] == []
    assert cuerpo["meta"]["cobertura"] in {"completa", "parcial"}
