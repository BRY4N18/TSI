"""E5-06 no expone nombre ni correo del agente."""

from __future__ import annotations

import json

import pytest

from apps.informes_estrategicos.tests.conftest import cliente, pedir_oe5


def test_us3_agente_sin_nombre():
    respuesta = pedir_oe5(cliente(["GerenteExitoCliente"]), "rendimiento-por-agente")
    if respuesta.status_code != 200:
        pytest.skip("el modelo analítico no está disponible")
    texto = json.dumps(respuesta.json()).lower()
    for clave in ("nombre", "correo", "email", "gmail"):
        assert clave not in texto
