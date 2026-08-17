"""T031, T037 — contrato de US1 y exclusión de dato sensible."""

from __future__ import annotations

import json

import pytest

from apps.informes_estrategicos.tests.conftest import (
    BASE,
    PERIODO,
    SENSIBLES,
    cliente,
    pedir,
)


@pytest.fixture
def director():
    return cliente(["DirectorOperaciones"])


class TestContratoUs1:
    def test_tiempo_global_tiene_la_forma(self, director):
        respuesta = pedir(director, "tiempo-respuesta-global")
        if respuesta.status_code != 200:
            pytest.skip("el modelo analítico no está disponible")
        cuerpo = respuesta.json()
        assert set(cuerpo) == {"data", "meta"}
        meta = cuerpo["meta"]
        assert "periodo" in meta and "cobertura" in meta
        assert "acotado_a" not in meta
        assert set(meta["periodo"]) == {"desde", "hasta", "granularidad", "parcial"}
        for fila in cuerpo["data"]:
            assert {"periodo", "casos_con_llegada", "excluidos_sin_llegada", "mediana_min", "p95_min"} <= set(fila)

    def test_por_severidad_tiene_la_forma(self, director):
        respuesta = pedir(director, "tiempo-respuesta-por-severidad")
        if respuesta.status_code != 200:
            pytest.skip("el modelo analítico no está disponible")
        for fila in respuesta.json()["data"]:
            assert {"periodo", "severidad", "orden", "casos", "mediana_min", "p95_min"} <= set(fila)

    def test_falta_granularidad_es_400_y_la_nombra(self, director):
        respuesta = director.get(
            f"{BASE}/tiempo-respuesta-global",
            {"desde": "2026-01-01", "hasta": "2026-12-31"},
        )
        assert respuesta.status_code == 400
        assert "granularidad" in respuesta.json()["detail"]


class TestSinDatoSensibleUs1:
    """T037 — con el rol de autoridad, no con uno acotado."""

    @pytest.mark.parametrize("informe", ["tiempo-respuesta-global", "tiempo-respuesta-por-severidad"])
    def test_ninguna_respuesta_contiene_coordenadas_ni_identidad(self, director, informe):
        respuesta = pedir(director, informe)
        if respuesta.status_code != 200:
            pytest.skip("el modelo analítico no está disponible")
        texto = json.dumps(respuesta.json()).lower()
        for sensible in SENSIBLES:
            assert sensible not in texto, f"'{informe}' expone '{sensible}'"
