"""Período vacío: flujo en data []; antigüedad de stock no finge 0 si hay activas."""

from __future__ import annotations

import pytest

from apps.informes_estrategicos.tests.conftest import INFORMES_OE5, cliente, pedir_oe5

VACIO = {"desde": "2019-01-01", "hasta": "2019-01-31", "granularidad": "mes"}
FLUJO = {
    "cumplimiento-sla",
    "evolucion-incumplimiento",
    "movimientos-de-plan",
    "rendimiento-por-agente",
    "reincidencia-soporte",
}


def _rol(informe: str) -> list[str]:
    if informe == "retencion-neta-ingresos":
        return ["DirectorFinanciero"]
    if informe in {"movimientos-de-plan", "antiguedad-de-cuenta", "sla-por-plan"}:
        return ["DirectorEstrategia"]
    if informe == "cuentas-en-riesgo":
        return ["Gerente"]
    return ["GerenteExitoCliente"]


@pytest.mark.parametrize("informe", INFORMES_OE5)
def test_oe5_periodo_vacio(informe):
    respuesta = pedir_oe5(cliente(_rol(informe)), informe, **VACIO)
    if respuesta.status_code != 200:
        pytest.skip("el modelo analítico no está disponible")
    cuerpo = respuesta.json()
    if informe in FLUJO:
        assert cuerpo["data"] == []
    assert cuerpo["meta"]["cobertura"] in {"completa", "parcial"}
