"""T033 — cumple es booleano en E3-02 y E3-10, null en E3-11. No copiar OE6."""

from __future__ import annotations

import pytest

from apps.informes_estrategicos.tests.conftest import cliente, pedir_oe3


class TestSemaforoUs1:
    def test_latencia_y_error_son_booleanos(self):
        director = cliente(["DirectorOperaciones"])
        for informe in ("latencia-asignacion", "tasa-error-registro"):
            respuesta = pedir_oe3(director, informe)
            if respuesta.status_code != 200:
                pytest.skip("el modelo analítico no está disponible")
            objetivo = respuesta.json()["meta"]["objetivo"]
            assert objetivo["tipo"] == "NORMATIVO"
            if respuesta.json()["data"]:
                assert isinstance(objetivo["cumple"], bool), (
                    f"'{informe}' debía semaforizar y cumple={objetivo['cumple']!r}"
                )

    def test_primer_intento_sigue_calibrar(self):
        respuesta = pedir_oe3(cliente(["DirectorOperaciones"]), "primer-intento")
        if respuesta.status_code != 200:
            pytest.skip("el modelo analítico no está disponible")
        objetivo = respuesta.json()["meta"]["objetivo"]
        assert objetivo["tipo"] == "CALIBRAR"
        assert objetivo["cumple"] is None
        assert not isinstance(objetivo["cumple"], bool)
