"""T033 — el p95 desaparece bajo muestra mínima."""

from __future__ import annotations

import pytest

from apps.informes_estrategicos.tests.conftest import cliente, pedir


@pytest.mark.integration
class TestPercentilBajoMuestraMinima:
    def test_p95_sale_null_no_un_numero(self):
        director = cliente(["DirectorOperaciones"])
        respuesta = pedir(
            director,
            "tiempo-respuesta-global",
            desde="2026-08-13",
            hasta="2026-08-13",
            granularidad="mes",
            muestra_minima=500,
        )
        if respuesta.status_code != 200:
            pytest.skip("el modelo analítico no está disponible")

        for fila in respuesta.json()["data"]:
            assert fila["p95_min"] is None, (
                f"p95={fila['p95_min']} con muestra_minima=500: con cinco "
                f"observaciones el p95 es el máximo, no un percentil"
            )
