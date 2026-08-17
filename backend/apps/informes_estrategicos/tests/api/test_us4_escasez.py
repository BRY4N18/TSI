"""T077 — con muestra insuficiente, E6-11 declara cobertura parcial."""

from __future__ import annotations

import pytest

from apps.informes_estrategicos.tests.conftest import cliente, pedir


@pytest.mark.integration
class TestEscasezEscaladas:
    def test_cobertura_parcial_bajo_muestra_minima(self):
        director = cliente(["DirectorOperaciones"])
        respuesta = pedir(
            director, "escaladas-de-severidad", muestra_minima=5
        )
        if respuesta.status_code != 200:
            pytest.skip("el modelo analítico no está disponible")

        meta = respuesta.json()["meta"]
        # La fuente tiene ~1 escalada en 4 252 casos. Con mínimo 5, es parcial.
        assert meta["cobertura"] == "parcial", (
            "un porcentaje cercano a cero se leería como «la severidad inicial "
            "acierta casi siempre» cuando lo que dice es que casi nadie usa la función"
        )
