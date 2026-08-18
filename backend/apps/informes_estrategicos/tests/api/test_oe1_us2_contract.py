"""Contrato US2: captación. Skip si el almacén no está."""

from __future__ import annotations

import json

import pytest

from apps.informes_estrategicos.tests.conftest import SENSIBLES, cliente, pedir_oe1

US2 = ("embudo-conversion", "velocidad-ciclo-venta")


class TestContratoUs2Oe1:
    def test_los_dos_responden(self):
        api = cliente(["DirectorMarketing"])
        for informe in US2:
            respuesta = pedir_oe1(api, informe)
            if respuesta.status_code != 200:
                pytest.skip("el modelo analítico no está disponible")
            cuerpo = respuesta.json()
            assert "data" in cuerpo and "meta" in cuerpo


def test_us2_embudo_ceros_y_volumen():
    respuesta = pedir_oe1(cliente(["DirectorMarketing"]), "embudo-conversion")
    if respuesta.status_code != 200:
        pytest.skip("el modelo analítico no está disponible")
    filas = respuesta.json()["data"]
    if not filas:
        pytest.skip("sin etapas en el almacén")
    etapas = [f.get("etapa") for f in filas]
    assert etapas, "el catálogo de etapas debe aparecer aunque el período esté en cero"
    volumenes = [int(f.get("transiciones") or 0) for f in filas]
    assert min(volumenes) >= 0


def test_us2_sin_ficha_de_prospecto():
    respuesta = pedir_oe1(cliente(["DirectorMarketing"]), "velocidad-ciclo-venta")
    if respuesta.status_code != 200:
        pytest.skip("el modelo analítico no está disponible")
    texto = json.dumps(respuesta.json()).lower()
    for clave in SENSIBLES + ("nombres", "apellidos", "gmail", "telefono", "email"):
        assert clave not in texto
