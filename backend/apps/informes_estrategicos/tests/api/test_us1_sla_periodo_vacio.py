"""Sin cerrados con compromiso: data [], no 0 %."""

from __future__ import annotations

import pytest

from apps.informes_estrategicos.tests.conftest import cliente, pedir_oe5

VACIO = {"desde": "2019-01-01", "hasta": "2019-01-31", "granularidad": "mes"}


def test_us1_sla_periodo_vacio_no_es_cero():
    respuesta = pedir_oe5(cliente(["GerenteExitoCliente"]), "cumplimiento-sla", **VACIO)
    if respuesta.status_code != 200:
        pytest.skip("el modelo analítico no está disponible")
    cuerpo = respuesta.json()
    assert cuerpo["data"] == []
    for fila in cuerpo["data"]:
        assert fila.get("pct_cumplimiento") not in {0, 0.0}
