"""Los seis bloqueados responden 404, no 200 vacío."""

from __future__ import annotations

import pytest

from apps.informes_estrategicos.tests.conftest import BLOQUEADOS_OE4, cliente, pedir_oe4


class TestBloqueadosOe4:
    @pytest.mark.parametrize("informe", BLOQUEADOS_OE4)
    def test_devuelve_404(self, informe):
        respuesta = pedir_oe4(cliente(["DirectorDatos"]), informe)
        assert respuesta.status_code == 404
        assert respuesta.json().get("data") != []
