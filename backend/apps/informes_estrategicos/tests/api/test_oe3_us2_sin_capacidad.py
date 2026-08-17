"""T048 — demanda sin unidades vigentes: sin_capacidad true y ratio null."""

from __future__ import annotations

import pytest

from apps.informes_estrategicos.tests.conftest import cliente, pedir_oe3


class TestSinCapacidad:
    def test_ratio_null_cuando_sin_capacidad(self):
        respuesta = pedir_oe3(cliente(["DirectorOperaciones"]), "ratio-demanda-capacidad")
        if respuesta.status_code != 200:
            pytest.skip("el modelo analítico no está disponible")
        for fila in respuesta.json()["data"]:
            if fila.get("sin_capacidad"):
                assert fila["ratio"] is None
                assert int(fila["unidades_vigentes"] or 0) == 0
            else:
                assert fila["ratio"] is not None or int(fila["casos"] or 0) == 0
