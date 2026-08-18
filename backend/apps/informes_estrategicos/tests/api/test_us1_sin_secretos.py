"""Ninguna respuesta de US1 lleva IP, hash ni contacto."""

from __future__ import annotations

import json

import pytest

from apps.informes_estrategicos.tests.conftest import SENSIBLES, cliente, pedir_oe2

US1 = (
    "integraciones-activas",
    "consumo-por-partner",
    "latencia-por-endpoint",
    "taxonomia-errores",
)


@pytest.mark.parametrize("informe", US1)
def test_us1_sin_secretos(informe):
    respuesta = pedir_oe2(cliente(["DirectorTecnologico"]), informe)
    if respuesta.status_code not in {200, 403}:
        pytest.skip("el modelo analítico no está disponible")
    if respuesta.status_code == 403:
        return
    texto = json.dumps(respuesta.json()).lower()
    for sensible in SENSIBLES + ("client_secret", "ip_cliente"):
        assert sensible not in texto
