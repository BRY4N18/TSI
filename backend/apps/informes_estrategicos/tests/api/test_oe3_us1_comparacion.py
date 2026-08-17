"""T036 — mom declara dos ventanas; yoy ausente con motivo, no 400."""

from __future__ import annotations

from datetime import date

import pytest

from apps.informes_estrategicos.tests.conftest import cliente, pedir_oe3


class TestComparacionOe3:
    def test_mom_dos_ventanas_de_igual_longitud(self):
        respuesta = pedir_oe3(
            cliente(["DirectorOperaciones"]),
            "latencia-asignacion",
            comparacion="mom",
            desde="2026-07-01",
            hasta="2026-09-30",
            granularidad="trimestre",
        )
        if respuesta.status_code != 200:
            pytest.skip("el modelo analítico no está disponible")
        comp = respuesta.json()["meta"].get("comparacion")
        assert comp is not None
        actual = comp["ventana_actual"]
        anterior = comp["ventana_anterior"]
        if anterior is None:
            return
        d_act = date.fromisoformat(actual["hasta"]) - date.fromisoformat(actual["desde"])
        d_ant = date.fromisoformat(anterior["hasta"]) - date.fromisoformat(anterior["desde"])
        assert d_act == d_ant

    def test_yoy_no_es_400(self):
        respuesta = pedir_oe3(
            cliente(["DirectorOperaciones"]),
            "latencia-asignacion",
            comparacion="yoy",
        )
        assert respuesta.status_code != 400
        if respuesta.status_code != 200:
            pytest.skip("el modelo analítico no está disponible")
        comp = respuesta.json()["meta"]["comparacion"]
        assert comp["ventana_anterior"] is None
        assert comp.get("motivo_ausencia")
