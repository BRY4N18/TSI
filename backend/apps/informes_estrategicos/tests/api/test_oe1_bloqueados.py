"""E1-05, E1-07 y E1-08 no se publican: 404, no 200 con cero."""

from __future__ import annotations

import pytest

from apps.informes_estrategicos.tests.conftest import BLOQUEADOS_OE1, cliente, pedir_oe1


class TestOe1Bloqueados:
    @pytest.mark.parametrize("informe", BLOQUEADOS_OE1)
    def test_bloqueados_son_404(self, informe):
        respuesta = pedir_oe1(cliente(["Gerente"]), informe)
        assert respuesta.status_code == 404
        assert respuesta.json().get("data") != []

    def test_alias_tambien_404(self):
        for alias in ("cac-por-canal", "mercados-activos", "cartera-mrr-por-mercado"):
            respuesta = pedir_oe1(cliente(["DirectorFinanciero"]), alias)
            assert respuesta.status_code == 404
