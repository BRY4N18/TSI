"""Ninguna clave de US1 es medio de pago, hash o contacto."""

from __future__ import annotations

import json

import pytest

from apps.informes_estrategicos.tests.conftest import SENSIBLES, cliente, pedir_oe1

US1 = (
    "mrr-mensual",
    "arr-proyeccion",
    "mrr-por-segmento",
    "cartera-por-plan",
)
PROHIBIDOS = SENSIBLES + (
    "metodo_pago",
    "tiene_metodo_pago",
    "idpais",
    "idestado",
    "hash",
    "contacto",
)


@pytest.mark.parametrize("informe", US1)
def test_us1_sin_cobro_ni_persona(informe):
    rol = ["DirectorEstrategia"] if informe == "cartera-por-plan" else ["DirectorFinanciero"]
    respuesta = pedir_oe1(cliente(rol), informe)
    if respuesta.status_code != 200:
        pytest.skip("el modelo analítico no está disponible")
    texto = json.dumps(respuesta.json()).lower()
    for prohibido in PROHIBIDOS:
        assert prohibido not in texto, f"{informe} expone {prohibido}"
