"""T034 — la suma por severidad iguala el total de casos con llegada."""

from __future__ import annotations

import pytest

from apps.informes_estrategicos.tests.conftest import cliente, pedir


@pytest.mark.integration
class TestSumaPorSeveridad:
    def test_la_suma_incluye_desconocido_y_cuadra_con_el_global(self):
        director = cliente(["DirectorOperaciones"])
        global_ = pedir(director, "tiempo-respuesta-global", granularidad="anio")
        por_sev = pedir(director, "tiempo-respuesta-por-severidad", granularidad="anio")
        if global_.status_code != 200 or por_sev.status_code != 200:
            pytest.skip("el modelo analítico no está disponible")

        total = sum(int(f["casos_con_llegada"]) for f in global_.json()["data"])
        suma = sum(int(f["casos"]) for f in por_sev.json()["data"])
        assert suma == total, (
            f"por severidad suma {suma} y el global tiene {total}: algún caso "
            f"se perdió o se duplicó (¿se filtró 'Desconocido'?)"
        )
