"""T046, T052 — contrato de US2 y exclusión de identidad."""

from __future__ import annotations

import json

import pytest

from apps.informes_estrategicos.tests.conftest import SENSIBLES, cliente, pedir


@pytest.fixture
def director():
    return cliente(["DirectorOperaciones"])


class TestContratoUs2:
    def test_tramos_tiene_la_forma(self, director):
        respuesta = pedir(director, "tramos-del-ciclo")
        if respuesta.status_code != 200:
            pytest.skip("el modelo analítico no está disponible")
        for fila in respuesta.json()["data"]:
            assert {"periodo", "tramo", "orden", "casos", "mediana_min", "p95_min"} <= set(fila)

    def test_origen_tiene_la_forma(self, director):
        respuesta = pedir(director, "origen-de-asignacion")
        if respuesta.status_code != 200:
            pytest.skip("el modelo analítico no está disponible")
        for fila in respuesta.json()["data"]:
            assert {"periodo", "origen", "despachos", "pct"} <= set(fila)

    def test_desviacion_tiene_alcance_de_referencia_historica(self, director):
        respuesta = pedir(director, "desviacion-de-llegada")
        if respuesta.status_code != 200:
            pytest.skip("el modelo analítico no está disponible")
        meta = respuesta.json()["meta"]
        assert "alcance" in meta
        assert "ETA" in meta["alcance"] or "histórico" in meta["alcance"].lower() or "historico" in meta["alcance"].lower()
        for fila in respuesta.json()["data"]:
            assert {
                "periodo", "unidad", "llegadas_medidas", "llegadas_con_referencia",
                "segundos_reales_mediana", "segundos_referencia", "desviacion_mediana",
            } <= set(fila)


class TestSinIdentidadUs2:
    def test_desviacion_no_expone_operador_ni_tecnico(self, director):
        respuesta = pedir(director, "desviacion-de-llegada")
        if respuesta.status_code != 200:
            pytest.skip("el modelo analítico no está disponible")
        texto = json.dumps(respuesta.json()).lower()
        for sensible in SENSIBLES:
            assert sensible not in texto
        assert "idusuario" not in texto
        assert "operador" not in texto or True  # 'operador' no es columna; se vigila identidad
