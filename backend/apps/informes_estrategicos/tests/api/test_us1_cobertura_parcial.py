"""Con n de demostración, cobertura parcial y falta nombra la muestra."""

from __future__ import annotations

import pytest

from apps.informes_estrategicos.tests.conftest import cliente, pedir_oe1


def test_us1_cobertura_parcial_nombra_muestra():
    respuesta = pedir_oe1(cliente(["DirectorFinanciero"]), "mrr-mensual")
    if respuesta.status_code != 200:
        pytest.skip("el modelo analítico no está disponible")
    meta = respuesta.json()["meta"]
    assert meta["cobertura"] == "parcial"
    falta = " ".join(meta.get("falta") or []).lower()
    assert "muestra" in falta or "umbral" in falta
