"""T082 — ningún meta.objetivo.cumple es booleano. Todas las metas son CALIBRAR."""

from __future__ import annotations

import pytest

from apps.informes_estrategicos.tests.conftest import INFORMES, cliente, pedir


@pytest.mark.integration
class TestNingunCumpleBooleano:
    @pytest.mark.parametrize("informe", INFORMES)
    def test_cumple_nunca_es_booleano(self, informe):
        director = cliente(["DirectorOperaciones"])
        extra = {}
        if informe == "rechazo-y-timeout-por-unidad":
            extra["top"] = 10
        respuesta = pedir(director, informe, **extra)
        if respuesta.status_code != 200:
            pytest.skip("el modelo analítico no está disponible")

        objetivo = respuesta.json()["meta"].get("objetivo")
        if objetivo is None:
            return
        assert objetivo["tipo"] == "CALIBRAR"
        assert objetivo["cumple"] is None
        assert not isinstance(objetivo["cumple"], bool)
