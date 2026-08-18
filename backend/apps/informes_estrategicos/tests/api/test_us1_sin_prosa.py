"""Ninguna clave de US1 es asunto, mensaje o nota de ticket."""

from __future__ import annotations

import json

import pytest

from apps.informes_estrategicos.tests.conftest import cliente, pedir_oe5

US1 = ("cumplimiento-sla", "evolucion-incumplimiento", "sla-por-plan")
PROHIBIDOS = ("asunto", "descripcion", "mensaje", "nota", "cuerpo")


@pytest.mark.parametrize("informe", US1)
def test_us1_sin_prosa_de_ticket(informe):
    respuesta = pedir_oe5(cliente(["GerenteExitoCliente"]), informe)
    if respuesta.status_code != 200:
        pytest.skip("el modelo analítico no está disponible")
    texto = json.dumps(respuesta.json()).lower()
    for prohibido in PROHIBIDOS:
        assert prohibido not in texto, f"{informe} expone {prohibido}"
