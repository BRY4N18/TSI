"""T014 — DirectorExpansion recibe 403 en despacho y 200 en capacidad."""

from __future__ import annotations

import pytest

from apps.informes_estrategicos.tests.conftest import cliente, pedir_oe3


class TestPermisosOe3:
    def test_operaciones_entra_en_latencia(self):
        respuesta = pedir_oe3(cliente(["DirectorOperaciones"]), "latencia-asignacion")
        assert respuesta.status_code != 403

    def test_expansion_recibe_403_en_latencia_no_una_tabla_vacia(self):
        respuesta = pedir_oe3(cliente(["DirectorExpansion"]), "latencia-asignacion")
        assert respuesta.status_code == 403, (
            f"DirectorExpansion recibió {respuesta.status_code} en latencia: "
            "un permiso de módulo concedería de más"
        )
        assert respuesta.json().get("data") != []

    def test_expansion_entra_en_ratio(self):
        respuesta = pedir_oe3(cliente(["DirectorExpansion"]), "ratio-demanda-capacidad")
        assert respuesta.status_code != 403

    def test_gerente_entra_en_ambos(self):
        for informe in ("latencia-asignacion", "ratio-demanda-capacidad"):
            assert pedir_oe3(cliente(["Gerente"]), informe).status_code != 403

    @pytest.mark.parametrize("roles", [["Operador"], ["Despacho"], ["Unidad"], ["Administrador"]])
    def test_operativo_recibe_403(self, roles):
        respuesta = pedir_oe3(cliente(roles), "latencia-asignacion")
        assert respuesta.status_code == 403
