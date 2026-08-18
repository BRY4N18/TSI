"""T074, T075 — carga entrante vs resuelta: saldo y días vacíos."""

from __future__ import annotations

import pytest
from rest_framework.test import APIClient

from core.jwt_utils import create_access_token
from core.repositories.informes_tacticos.catalogo_consultas import cargar
from core.repositories.informes_tacticos.modelo_repository import ModeloRepository

BASE = "/api/v1/informes-tacticos/soporte/carga-entrante-resuelta"
SQL = cargar("ot20_carga_entrante_vs_resuelta", departamento="soporte")


@pytest.fixture(autouse=True)
def _pinot_en_memoria(mock_pinot, mock_kafka):
    return mock_pinot


def test_la_consulta_rellena_dias_vacios():
    assert "WITH FILL" in SQL


def test_un_dia_con_mas_aperturas_da_saldo_positivo_y_acumulado_creciente(monkeypatch):
    monkeypatch.setattr(
        ModeloRepository,
        "ejecutar",
        lambda *a, **k: [
            {"dia": "2026-08-01", "creados": 3, "resueltos": 1, "neto_acumulado": 2},
            {"dia": "2026-08-02", "creados": 1, "resueltos": 0, "neto_acumulado": 3},
        ],
    )
    api = APIClient()
    api.credentials(
        HTTP_AUTHORIZATION=f"Bearer {create_access_token(user_id=1, roles=['GerenteExitoCliente'], session_id=1)}"
    )
    filas = api.get(f"{BASE}?desde=2026-08-01&hasta=2026-08-02").json()["data"]["resultados"]
    assert filas[0]["creados"] - filas[0]["resueltos"] > 0
    assert filas[1]["neto_acumulado"] > filas[0]["neto_acumulado"]


def test_un_dia_sin_actividad_aparece_con_cero(monkeypatch):
    monkeypatch.setattr(
        ModeloRepository,
        "ejecutar",
        lambda *a, **k: [
            {"dia": "2026-08-01", "creados": 2, "resueltos": 2, "neto_acumulado": 0},
            {"dia": "2026-08-02", "creados": 0, "resueltos": 0, "neto_acumulado": 0},
            {"dia": "2026-08-03", "creados": 1, "resueltos": 0, "neto_acumulado": 1},
        ],
    )
    api = APIClient()
    api.credentials(
        HTTP_AUTHORIZATION=f"Bearer {create_access_token(user_id=1, roles=['GerenteExitoCliente'], session_id=1)}"
    )
    dias = {str(f["dia"])[:10]: f for f in api.get(f"{BASE}?desde=2026-08-01&hasta=2026-08-03").json()["data"]["resultados"]}
    assert dias["2026-08-02"]["creados"] == 0
    assert dias["2026-08-02"]["resueltos"] == 0
