"""T050 — E3-13 analiza todas las posiciones, no las 10 000 del legado."""

from __future__ import annotations

import pytest

from apps.informes_estrategicos.tests.conftest import cliente, pedir_oe3


class TestSenalCompleta:
    def test_huecos_del_orden_de_miles(self):
        respuesta = pedir_oe3(
            cliente(["DirectorExpansion"]),
            "perdida-de-senal",
            granularidad="anio",
        )
        if respuesta.status_code != 200:
            pytest.skip("el modelo analítico no está disponible")
        huecos = sum(int(f.get("huecos") or 0) for f in respuesta.json()["data"])
        assert huecos > 714, (
            f"solo {huecos} huecos: el legado truncaba a 714. "
            "Si se volvió a aplicar un LIMIT, las cifras bajan en silencio"
        )
        assert huecos >= 3000, f"{huecos} huecos, se esperaban ~3942"
