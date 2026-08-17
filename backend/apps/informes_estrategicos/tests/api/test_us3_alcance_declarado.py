"""T066 — E6-09 no responde 200 sin meta.alcance."""

from __future__ import annotations

import pytest

from apps.informes_estrategicos.tests.conftest import cliente, pedir


@pytest.mark.integration
class TestAlcanceDeclarado:
    def test_cierres_forzados_declara_alcance_y_cobertura_parcial(self):
        director = cliente(["DirectorOperaciones"])
        respuesta = pedir(director, "cierres-forzados")
        if respuesta.status_code != 200:
            pytest.skip("el modelo analítico no está disponible")

        meta = respuesta.json()["meta"]
        assert "alcance" in meta and meta["alcance"], (
            "un 1 de 3310 sin declaración se lee como «esto casi no pasa» "
            "cuando la definición pedida da 451"
        )
        assert meta["cobertura"] == "parcial"
        assert "retiro manual desde central" in meta.get("falta", [])
