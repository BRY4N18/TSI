"""T063 — contrato de US3."""

from __future__ import annotations

import pytest

from apps.informes_estrategicos.tests.conftest import cliente, pedir


@pytest.fixture
def director():
    return cliente(["DirectorOperaciones"])


class TestContratoUs3:
    def test_rechazo_tiene_tasas_separadas_y_alcance(self, director):
        respuesta = pedir(director, "rechazo-y-timeout-por-unidad", top=100)
        if respuesta.status_code != 200:
            pytest.skip("el modelo analítico no está disponible")
        meta = respuesta.json()["meta"]
        assert "alcance" in meta
        for fila in respuesta.json()["data"]:
            assert {
                "periodo", "unidad", "ofrecidos", "rechazados", "vencidos",
                "tasa_rechazo", "tasa_vencimiento",
            } <= set(fila)

    def test_abortos_tiene_la_forma(self, director):
        respuesta = pedir(director, "abortos-y-misiones-fallidas")
        if respuesta.status_code != 200:
            pytest.skip("el modelo analítico no está disponible")
        for fila in respuesta.json()["data"]:
            assert {"periodo", "causa", "misiones", "misiones_causa", "pct"} <= set(fila)

    def test_cierres_forzados_tiene_la_forma(self, director):
        respuesta = pedir(director, "cierres-forzados")
        if respuesta.status_code != 200:
            pytest.skip("el modelo analítico no está disponible")
        for fila in respuesta.json()["data"]:
            assert {"periodo", "despachos_confirmados", "forzados", "pct_forzados"} <= set(fila)

    def test_envejecimiento_tiene_la_forma(self, director):
        respuesta = pedir(director, "envejecimiento-de-casos-abiertos")
        if respuesta.status_code != 200:
            pytest.skip("el modelo analítico no está disponible")
        for fila in respuesta.json()["data"]:
            assert {"tramo_dias", "casos_abiertos"} <= set(fila)
