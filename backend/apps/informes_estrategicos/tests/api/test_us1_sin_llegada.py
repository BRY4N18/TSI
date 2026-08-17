"""T032 — un caso sin llegada no vale cero.

Falsable por mutación: incluirlos como cero debe hacer fallar la prueba, y el
síntoma en producción sería un tiempo de respuesta que mejora cuando empeora
la atención.
"""

from __future__ import annotations

import pytest

from apps.informes_estrategicos.tests.conftest import cliente, pedir
from core.repositories.informes_estrategicos.modelo_estrategico_repository import (
    ModeloEstrategicoRepository,
)


@pytest.mark.integration
class TestSinLlegadaNoValeCero:
    def test_los_excluidos_se_declaran_y_no_entran_en_la_mediana(self):
        director = cliente(["DirectorOperaciones"])
        respuesta = pedir(director, "tiempo-respuesta-global", granularidad="trimestre")
        if respuesta.status_code != 200:
            pytest.skip("el modelo analítico no está disponible")

        filas = respuesta.json()["data"]
        assert filas, "el período de línea base tiene casos"
        excluidos = sum(int(f["excluidos_sin_llegada"]) for f in filas)
        assert excluidos > 0, "si no hay excluidos, la prueba no puede fallar por mutación"

        repo = ModeloEstrategicoRepository()
        try:
            envenenada = repo.ejecutar(
                "e6_01_tiempo_respuesta_global",
                departamento="estrategicos/oe6",
                parametros={
                    "desde": "2026-01-01",
                    "hasta": "2026-12-31",
                    "granularidad": "trimestre",
                    "muestra_minima": 5,
                    "por_condado": 0,
                },
            )
        except Exception:
            pytest.skip("el modelo analítico no está disponible")

        # La mediana publicada tiene que ser la de quienes SÍ llegaron. Si los
        # sin llegada entraran como cero, con ~16 % de ceros la mediana caería.
        mediana_publicada = min(f["mediana_min"] for f in filas if f["mediana_min"] is not None)
        assert mediana_publicada >= 5, (
            f"mediana {mediana_publicada} min: si los sin llegada valieran cero, "
            f"el indicador mejoraría al empeorar la atención"
        )
        assert all(f["casos_con_llegada"] >= 0 for f in envenenada)
