"""E2-06 no se publica: 404, no 200 vacío."""

from __future__ import annotations

import pytest

from apps.informes_estrategicos.tests.conftest import BLOQUEADOS_OE2, cliente, pedir_oe2


class TestOe2Bloqueados:
    @pytest.mark.parametrize("informe", BLOQUEADOS_OE2)
    def test_disponibilidad_es_404(self, informe):
        respuesta = pedir_oe2(cliente(["Gerente"]), informe)
        assert respuesta.status_code == 404
        assert respuesta.json().get("data") != []

    def test_alias_uptime_tambien_404(self):
        respuesta = pedir_oe2(cliente(["DirectorTecnologico"]), "disponibilidad-api")
        assert respuesta.status_code == 404
