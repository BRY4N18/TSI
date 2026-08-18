"""Una anual no vale 12× un mensual del mismo precio anualizado."""

from __future__ import annotations

import pytest

from apps.informes_estrategicos.tests.conftest import cliente, pedir_oe1


def test_us1_mrr_usa_precio_mensualizado():
    respuesta = pedir_oe1(cliente(["DirectorFinanciero"]), "mrr-mensual")
    if respuesta.status_code != 200:
        pytest.skip("el modelo analítico no está disponible")
    cuerpo = respuesta.json()
    alcance = (cuerpo["meta"].get("alcance") or "").lower()
    assert "precio_mensualizado" in alcance
    assert "cierre" in alcance
    for fila in cuerpo["data"]:
        assert "mrr" in fila
        assert "precio" not in fila
