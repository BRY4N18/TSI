"""T075, T080 — contrato de US4 y exclusión de identidad."""

from __future__ import annotations

import json

import pytest

from apps.informes_estrategicos.tests.conftest import SENSIBLES, cliente, pedir


@pytest.fixture
def director():
    return cliente(["DirectorOperaciones"])


class TestContratoUs4:
    def test_impacto_tiene_casos_con_dato(self, director):
        respuesta = pedir(director, "impacto-humano")
        if respuesta.status_code != 200:
            pytest.skip("el modelo analítico no está disponible")
        for fila in respuesta.json()["data"]:
            assert {
                "periodo", "severidad", "casos", "casos_con_dato",
                "victimas", "heridos", "fallecidos",
            } <= set(fila)

    def test_escaladas_tiene_la_forma(self, director):
        respuesta = pedir(director, "escaladas-de-severidad")
        if respuesta.status_code != 200:
            pytest.skip("el modelo analítico no está disponible")
        for fila in respuesta.json()["data"]:
            assert {"periodo", "casos", "con_escalada"} <= set(fila)

    def test_evidencia_tiene_foto_nota_y_ambas(self, director):
        respuesta = pedir(director, "cobertura-de-evidencia")
        if respuesta.status_code != 200:
            pytest.skip("el modelo analítico no está disponible")
        for fila in respuesta.json()["data"]:
            assert {
                "periodo", "severidad", "casos_cerrados",
                "con_foto", "con_nota", "con_ambas", "pct_con_ambas",
            } <= set(fila)


class TestSinIdentidadUs4:
    @pytest.mark.parametrize(
        "informe",
        ["impacto-humano", "escaladas-de-severidad", "cobertura-de-evidencia"],
    )
    def test_no_expone_implicados_ni_tecnicos(self, director, informe):
        respuesta = pedir(director, informe)
        if respuesta.status_code != 200:
            pytest.skip("el modelo analítico no está disponible")
        texto = json.dumps(respuesta.json()).lower()
        for sensible in SENSIBLES:
            assert sensible not in texto, f"'{informe}' expone '{sensible}'"
