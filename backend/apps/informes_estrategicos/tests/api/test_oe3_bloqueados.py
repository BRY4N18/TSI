"""T053, T057 — los siete bloqueados responden 404, no 200 vacío."""

from __future__ import annotations

import pytest

from apps.informes_estrategicos.tests.conftest import BLOQUEADOS_OE3, cliente, pedir_oe3


class TestBloqueadosOe3:
    @pytest.mark.parametrize("informe", BLOQUEADOS_OE3)
    def test_devuelve_404(self, informe):
        respuesta = pedir_oe3(cliente(["DirectorOperaciones"]), informe)
        assert respuesta.status_code == 404, (
            f"'{informe}' respondió {respuesta.status_code}: publicarlo vacío "
            "o con ceros afirmaría algo que el sistema no sabe. E3-04 "
            "compararía contra 1970."
        )
        assert respuesta.json().get("data") != []
