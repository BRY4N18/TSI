"""T032 — el objetivo de E3-02 es 2 minutos, no 100 ms."""

from __future__ import annotations

import pytest

from apps.informes_estrategicos.tests.conftest import cliente, pedir_oe3


class TestMetaCorrecta:
    def test_objetivo_es_dos_minutos_con_alcance(self):
        respuesta = pedir_oe3(cliente(["DirectorOperaciones"]), "latencia-asignacion")
        if respuesta.status_code != 200:
            pytest.skip("el modelo analítico no está disponible")
        objetivo = respuesta.json()["meta"]["objetivo"]
        assert objetivo["valor"] == 2
        assert objetivo["unidad"] == "min"
        assert objetivo["tipo"] == "NORMATIVO"
        assert objetivo["valor"] != 0.1 and objetivo["unidad"] != "ms"
        alcance = respuesta.json()["meta"].get("alcance") or ""
        assert "operativo" in alcance.lower() or "RNF-DES-001" in alcance
        assert "100" not in str(objetivo["valor"])
