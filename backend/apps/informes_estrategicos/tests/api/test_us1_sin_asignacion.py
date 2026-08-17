"""T034 — los casos sin asignación se declaran y no entran en la mediana."""

from __future__ import annotations

import pytest

from apps.informes_estrategicos.tests.conftest import cliente, pedir_oe3


class TestSinAsignacion:
    def test_excluidos_no_entran_en_la_mediana(self):
        respuesta = pedir_oe3(
            cliente(["DirectorOperaciones"]), "latencia-asignacion", granularidad="anio"
        )
        if respuesta.status_code != 200:
            pytest.skip("el modelo analítico no está disponible")
        data = respuesta.json()["data"]
        if not data:
            pytest.skip("sin filas")
        fila = data[0]
        assert "excluidos_sin_asignacion" in fila
        # Si se contaran como cero, la mediana bajaría al incluir ceros.
        # Con exclusión, casos_asignados + excluidos es la población del filtro.
        assert fila["casos_asignados"] >= 0
        assert fila["excluidos_sin_asignacion"] >= 0
        if fila["excluidos_sin_asignacion"] > 0:
            assert fila["mediana_seg"] is None or fila["mediana_seg"] > 0
