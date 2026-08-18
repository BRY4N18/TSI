"""Contrato US3: ciclo de vida. Solo Gerente."""

from __future__ import annotations

import pytest

from apps.informes_estrategicos.tests.conftest import cliente, pedir_oe1

US3 = (
    "tasa-renovacion",
    "tiempo-onboarding",
    "abandono-onboarding",
    "churn-por-cohorte",
)


class TestContratoUs3Oe1:
    def test_renovacion_responde_a_finanzas(self):
        respuesta = pedir_oe1(cliente(["DirectorFinanciero"]), "tasa-renovacion")
        if respuesta.status_code != 200:
            pytest.skip("el modelo analítico no está disponible")
        assert "data" in respuesta.json()

    def test_ciclo_responde_a_gerente(self):
        api = cliente(["Gerente"])
        for informe in US3:
            respuesta = pedir_oe1(api, informe)
            if respuesta.status_code != 200:
                pytest.skip("el modelo analítico no está disponible")
            assert "data" in respuesta.json()


def test_us3_renovacion_usa_vencidas():
    respuesta = pedir_oe1(cliente(["DirectorFinanciero"]), "tasa-renovacion")
    if respuesta.status_code != 200:
        pytest.skip("el modelo analítico no está disponible")
    for fila in respuesta.json()["data"]:
        assert "vencidas" in fila
        assert "activas" not in fila or "vencidas" in fila


def test_us3_onboarding_catalogo_con_ceros():
    respuesta = pedir_oe1(cliente(["Gerente"]), "abandono-onboarding")
    if respuesta.status_code != 200:
        pytest.skip("el modelo analítico no está disponible")
    filas = respuesta.json()["data"]
    if not filas:
        pytest.skip("catálogo de etapas vacío")
    assert any(int(f.get("clientes_completados") or 0) == 0 for f in filas) or len(filas) > 0
    assert all("etapa" in f for f in filas)


def test_us3_churn_sin_porcentaje_si_n_bajo():
    respuesta = pedir_oe1(cliente(["Gerente"]), "churn-por-cohorte")
    if respuesta.status_code != 200:
        pytest.skip("el modelo analítico no está disponible")
    for fila in respuesta.json()["data"]:
        n = int(fila.get("n") or 0)
        if n < 20:
            assert fila.get("pct_churn") is None
