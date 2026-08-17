"""T035 — E3-10 no responde 200 sin campos_comprobados."""

from __future__ import annotations

import pytest

from apps.informes_estrategicos.tests.conftest import cliente, pedir_oe3


class TestCamposComprobados:
    def test_cada_fila_declara_que_mira(self):
        respuesta = pedir_oe3(cliente(["DirectorOperaciones"]), "tasa-error-registro")
        if respuesta.status_code != 200:
            pytest.skip("el modelo analítico no está disponible")
        data = respuesta.json()["data"]
        assert data, "sin filas no se puede comprobar la lista"
        for fila in data:
            campos = fila.get("campos_comprobados")
            assert campos, (
                "tasa-error-registro respondió 200 sin campos_comprobados: "
                "un 0 % permanente se lee como registro perfecto"
            )
            assert "severidad" in campos
