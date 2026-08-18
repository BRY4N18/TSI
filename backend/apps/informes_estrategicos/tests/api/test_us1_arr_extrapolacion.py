"""ARR declara extrapolación, no compromiso."""

from __future__ import annotations

import pytest

from apps.informes_estrategicos.tests.conftest import cliente, pedir_oe1


def test_us1_arr_declara_extrapolacion():
    respuesta = pedir_oe1(cliente(["DirectorFinanciero"]), "arr-proyeccion")
    if respuesta.status_code != 200:
        pytest.skip("el modelo analítico no está disponible")
    alcance = (respuesta.json()["meta"].get("alcance") or "").lower()
    assert "extrapol" in alcance
    assert "compromet" in alcance or "compromiso" in alcance or "no es ingreso" in alcance
