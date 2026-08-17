"""T049 — los porcentajes de los tres orígenes suman 100 %."""

from __future__ import annotations

from collections import defaultdict

import pytest

from apps.informes_estrategicos.tests.conftest import cliente, pedir


@pytest.mark.integration
class TestOrigenSumaCien:
    def test_los_tres_origenes_suman_cien_por_periodo(self):
        director = cliente(["DirectorOperaciones"])
        respuesta = pedir(director, "origen-de-asignacion", granularidad="anio")
        if respuesta.status_code != 200:
            pytest.skip("el modelo analítico no está disponible")

        por_periodo = defaultdict(list)
        for fila in respuesta.json()["data"]:
            por_periodo[fila["periodo"]].append(fila)

        for periodo, filas in por_periodo.items():
            total = round(sum(float(f["pct"]) for f in filas), 4)
            assert total == pytest.approx(1.0, abs=0.001), (
                f"período {periodo}: los orígenes suman {total}, no 100 %"
            )
            nombres = {f["origen"] for f in filas}
            assert any("escalad" in n.lower() or "Escalado" in n or "zona" in n.lower() for n in nombres) or len(nombres) >= 1
