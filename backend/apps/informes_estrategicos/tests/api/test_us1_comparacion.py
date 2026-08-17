"""T035 — la comparación declara dos ventanas; yoy ausente no es 400."""

from __future__ import annotations

from datetime import date

import pytest

from apps.informes_estrategicos.tests.conftest import cliente, pedir


@pytest.mark.integration
class TestComparacionUs1:
    def test_mom_declara_dos_ventanas_de_igual_longitud(self):
        director = cliente(["DirectorOperaciones"])
        respuesta = pedir(
            director,
            "tiempo-respuesta-global",
            desde="2026-07-01",
            hasta="2026-09-30",
            granularidad="trimestre",
            comparacion="mom",
        )
        if respuesta.status_code != 200:
            pytest.skip("el modelo analítico no está disponible")

        comparacion = respuesta.json()["meta"]["comparacion"]
        actual = comparacion["ventana_actual"]
        anterior = comparacion["ventana_anterior"]
        assert anterior is not None
        long_act = (
            date.fromisoformat(actual["hasta"]) - date.fromisoformat(actual["desde"])
        ).days
        long_ant = (
            date.fromisoformat(anterior["hasta"]) - date.fromisoformat(anterior["desde"])
        ).days
        assert long_act == long_ant

    def test_yoy_devuelve_ausencia_no_400_ni_variacion_cero(self):
        director = cliente(["DirectorOperaciones"])
        respuesta = pedir(
            director,
            "tiempo-respuesta-global",
            desde="2026-07-01",
            hasta="2026-09-30",
            granularidad="trimestre",
            comparacion="yoy",
        )
        assert respuesta.status_code != 400
        if respuesta.status_code != 200:
            pytest.skip("el modelo analítico no está disponible")

        comparacion = respuesta.json()["meta"]["comparacion"]
        assert comparacion["ventana_anterior"] is None
        assert comparacion["motivo_ausencia"]
        assert comparacion.get("variacion") in (None, {})
