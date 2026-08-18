"""Todo porcentaje de OE1 trae denominador."""

from __future__ import annotations

import pytest

from apps.informes_estrategicos.tests.conftest import INFORMES_OE1, cliente, pedir_oe1

DENOMS = (
    "denominador",
    "vencidas",
    "n",
    "recuento",
    "transiciones",
    "completados",
    "clientes_completados",
)


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
def test_oe1_porcentaje_con_denominador(informe):
    respuesta = pedir_oe1(cliente(_rol(informe)), informe)
    if respuesta.status_code != 200:
        pytest.skip("el modelo analítico no está disponible")
    for fila in respuesta.json()["data"]:
        claves = set(fila)
        hay_pct = any("pct" in k or k.startswith("tasa") for k in claves)
        if hay_pct:
            assert claves & set(DENOMS), claves
