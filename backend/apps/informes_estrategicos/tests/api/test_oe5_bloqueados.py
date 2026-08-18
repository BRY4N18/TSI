"""E5-01/11 y las cuatro de OE1 no se publican en OE5: 404."""

from __future__ import annotations

import pytest

from apps.informes_estrategicos.tests.conftest import BLOQUEADOS_OE5, cliente, pedir_oe5


class TestOe5Bloqueados:
    @pytest.mark.parametrize("informe", BLOQUEADOS_OE5)
    def test_bloqueados_y_referencias_son_404(self, informe):
        respuesta = pedir_oe5(cliente(["Gerente"]), informe)
        assert respuesta.status_code == 404
        assert respuesta.json().get("data") != []

    def test_referencia_oe1_nombra_el_camino(self):
        respuesta = pedir_oe5(cliente(["Gerente"]), "tasa-renovacion")
        assert respuesta.status_code == 404
        texto = str(respuesta.json()).lower()
        assert "oe1" in texto
