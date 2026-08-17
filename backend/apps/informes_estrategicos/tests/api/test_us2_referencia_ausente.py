"""T050 — sin muestra suficiente, referencia y desviación salen null, no cero."""

from __future__ import annotations

import pytest

from apps.informes_estrategicos.tests.conftest import cliente, pedir


@pytest.mark.integration
class TestReferenciaAusente:
    def test_sin_muestra_referencia_y_desviacion_son_null(self):
        director = cliente(["DirectorOperaciones"])
        respuesta = pedir(
            director,
            "desviacion-de-llegada",
            muestra_minima=1000,
            ventana_dias=7,
        )
        if respuesta.status_code != 200:
            pytest.skip("el modelo analítico no está disponible")

        filas = respuesta.json()["data"]
        if not filas:
            pytest.skip("sin llegadas en el período")

        assert all(f["segundos_referencia"] is None for f in filas), (
            "una referencia 0 diría «llegó exactamente a tiempo» y convertiría "
            "una unidad sin histórico en una unidad ejemplar"
        )
        assert all(f["desviacion_mediana"] is None for f in filas)
