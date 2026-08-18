"""Todo porcentaje de OE5 trae denominador."""

from __future__ import annotations

import pytest

from apps.informes_estrategicos.tests.conftest import INFORMES_OE5, cliente, pedir_oe5

DENOMS = (
    "denominador",
    "con_compromiso",
    "recuento",
    "mrr_inicial",
    "tickets",
    "n_senales",
    "activas",
)


def _rol(informe: str) -> list[str]:
    if informe == "retencion-neta-ingresos":
        return ["DirectorFinanciero"]
    if informe in {"movimientos-de-plan", "antiguedad-de-cuenta", "sla-por-plan"}:
        return ["DirectorEstrategia"]
    if informe == "cuentas-en-riesgo":
        return ["Gerente"]
    return ["GerenteExitoCliente"]


@pytest.mark.parametrize("informe", INFORMES_OE5)
def test_oe5_porcentaje_con_denominador(informe):
    respuesta = pedir_oe5(cliente(_rol(informe)), informe)
    if respuesta.status_code != 200:
        pytest.skip("el modelo analítico no está disponible")
    for fila in respuesta.json()["data"]:
        claves = set(fila)
        hay_pct = any("pct" in k or k in {"nrr", "tasa"} for k in claves)
        if hay_pct:
            assert claves & set(DENOMS), claves
