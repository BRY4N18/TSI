"""DirectorOperaciones no ve inteligencia vendible; DirectorDatos sí."""

from __future__ import annotations

import pytest

from apps.informes_estrategicos.tests.conftest import cliente, pedir_oe4

EXPEDIENTE = "indice-calidad-historico"
VENDIBLE = "concentracion-siniestralidad"


class TestPermisosOe4:
    def test_datos_entra_en_vendible(self):
        assert pedir_oe4(cliente(["DirectorDatos"]), VENDIBLE).status_code != 403

    def test_operaciones_recibe_403_en_vendible(self):
        respuesta = pedir_oe4(cliente(["DirectorOperaciones"]), VENDIBLE)
        assert respuesta.status_code == 403
        assert respuesta.json().get("data") != []

    def test_operaciones_entra_en_expediente(self):
        assert pedir_oe4(cliente(["DirectorOperaciones"]), EXPEDIENTE).status_code != 403

    def test_gerente_entra_en_ambos(self):
        for informe in (EXPEDIENTE, VENDIBLE):
            assert pedir_oe4(cliente(["Gerente"]), informe).status_code != 403

    @pytest.mark.parametrize("roles", [["Operador"], ["Administrador"], ["DirectorExpansion"]])
    def test_ajenos_reciben_403(self, roles):
        assert pedir_oe4(cliente(roles), EXPEDIENTE).status_code == 403
