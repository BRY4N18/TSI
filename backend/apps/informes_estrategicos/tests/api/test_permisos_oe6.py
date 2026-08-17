"""T024 — DirectorOperaciones y Gerente entran; el resto recibe 403, no 200 vacío."""

from __future__ import annotations

import pytest

from apps.informes_estrategicos.tests.conftest import BASE, cliente, pedir


class TestPermisosOe6:
    @pytest.mark.parametrize("roles", [["DirectorOperaciones"], ["Gerente"]])
    def test_entran_la_autoridad_y_el_gerente(self, roles):
        respuesta = pedir(cliente(roles), "tiempo-respuesta-global")
        assert respuesta.status_code != 403, (
            f"{roles} recibió 403 y es autoridad de OE6"
        )

    @pytest.mark.parametrize(
        "roles",
        [
            ["Operador"],
            ["Despacho"],
            ["Unidad"],
            ["Administrador"],
            ["DirectorFinanciero"],
        ],
    )
    def test_cualquier_otro_rol_recibe_403_no_una_tabla_vacia(self, roles):
        respuesta = pedir(cliente(roles), "tiempo-respuesta-global")
        assert respuesta.status_code == 403, (
            f"{roles} recibió {respuesta.status_code} en vez de 403: un 200 con "
            f"data vacía diría «no hay datos» donde el sistema quiso decir "
            f"«no tienes acceso»"
        )
        assert respuesta.json().get("data") != []
