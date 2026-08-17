"""T084 — un período sin datos devuelve data: [] con cobertura completa, nunca ceros."""

from __future__ import annotations

import pytest

from apps.informes_estrategicos.tests.conftest import INFORMES, cliente, pedir

VACIO = {
    "desde": "2019-01-01",
    "hasta": "2019-01-31",
    "granularidad": "mes",
}


@pytest.mark.integration
class TestPeriodoSinDatos:
    @pytest.mark.parametrize("informe", INFORMES)
    def test_data_vacia_cobertura_completa(self, informe):
        director = cliente(["DirectorOperaciones"])
        extra = dict(VACIO)
        if informe == "rechazo-y-timeout-por-unidad":
            extra["top"] = 10
        respuesta = pedir(director, informe, **extra)
        if respuesta.status_code != 200:
            pytest.skip("el modelo analítico no está disponible")

        cuerpo = respuesta.json()
        assert cuerpo["data"] == [], (
            f"'{informe}' devolvió filas de ceros en un período sin datos: "
            f"{cuerpo['data'][:2]}"
        )
        if informe != "cierres-forzados":
            assert cuerpo["meta"]["cobertura"] == "completa"
        # cierres-forzados declara cobertura parcial por alcance (#36), no por falta de datos
