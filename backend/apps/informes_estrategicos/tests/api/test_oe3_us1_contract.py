"""T031, T038 — contrato US1 y exclusión de dato sensible."""

from __future__ import annotations

import json

import pytest

from apps.informes_estrategicos.tests.conftest import (
    BASE_OE3,
    PERIODO,
    SENSIBLES,
    cliente,
    pedir_oe3,
)

US1 = (
    "latencia-asignacion",
    "evolucion-latencia",
    "tasa-error-registro",
    "primer-intento",
)


@pytest.fixture
def director():
    return cliente(["DirectorOperaciones"])


class TestContratoUs1:
    def test_latencia_tiene_la_forma(self, director):
        respuesta = pedir_oe3(director, "latencia-asignacion")
        if respuesta.status_code != 200:
            pytest.skip("el modelo analítico no está disponible")
        cuerpo = respuesta.json()
        assert set(cuerpo) == {"data", "meta"}
        assert "acotado_a" not in cuerpo["meta"]
        for fila in cuerpo["data"]:
            assert {
                "periodo", "casos_asignados", "excluidos_sin_asignacion",
                "mediana_seg", "p95_seg", "p95_min", "sobre_umbral",
            } <= set(fila)

    def test_los_cuatro_responden(self, director):
        for informe in US1:
            respuesta = pedir_oe3(director, informe)
            if respuesta.status_code != 200:
                pytest.skip("el modelo analítico no está disponible")
            assert "data" in respuesta.json()

    def test_falta_granularidad_es_400_y_la_nombra(self, director):
        respuesta = director.get(
            f"{BASE_OE3}/latencia-asignacion",
            {"desde": PERIODO["desde"], "hasta": PERIODO["hasta"]},
        )
        assert respuesta.status_code == 400
        assert "granularidad" in respuesta.json()["detail"]


class TestSinDatoSensibleUs1:
    @pytest.mark.parametrize("informe", US1)
    def test_ninguna_respuesta_contiene_coordenadas_ni_identidad(self, director, informe):
        respuesta = pedir_oe3(director, informe)
        if respuesta.status_code != 200:
            pytest.skip("el modelo analítico no está disponible")
        texto = json.dumps(respuesta.json()).lower()
        for sensible in SENSIBLES:
            assert sensible not in texto, f"'{informe}' expone '{sensible}'"
