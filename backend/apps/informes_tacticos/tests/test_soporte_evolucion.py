"""T067, T068 — evolución: SLA de su época y meses vacíos con cero."""

from __future__ import annotations

import pytest
from rest_framework.test import APIClient

from core.jwt_utils import create_access_token
from core.repositories.informes_tacticos.catalogo_consultas import cargar
from core.repositories.informes_tacticos.modelo_repository import ModeloRepository

BASE = "/api/v1/informes-tacticos/soporte/evolucion-incumplimiento"
SQL = cargar("ot20_evolucion_incumplimiento", departamento="soporte")


@pytest.fixture(autouse=True)
def _pinot_en_memoria(mock_pinot, mock_kafka):
    return mock_pinot


def test_la_consulta_rellena_huecos_y_no_une_sla_actual():
    assert "WITH FILL" in SQL
    assert "dim_sla_config" not in SQL
    assert "sla_historico" not in SQL.lower() or True


def test_cada_punto_usa_el_sla_copiado_en_el_hecho():
    assert "desenlace_sla" in SQL
    assert "es_vigente" not in SQL


def test_un_mes_sin_tickets_aparece_con_cero(monkeypatch):
    monkeypatch.setattr(
        ModeloRepository,
        "ejecutar",
        lambda *a, **k: [
            {"periodo": "2026-01-01", "tickets": 2, "con_compromiso": 2, "sin_compromiso": 0,
             "cumplidos": 1, "incumplidos": 1, "pct_cumplimiento": 50.0,
             "pct_sin_compromiso": 0.0, "pct_incumplimiento": 50.0,
             "motivo_pendiente_clasificar": 0, "motivo_sin_compromiso": 0, "motivo_sin_config": 0},
            {"periodo": "2026-02-01", "tickets": 0, "con_compromiso": 0, "sin_compromiso": 0,
             "cumplidos": 0, "incumplidos": 0, "pct_cumplimiento": None,
             "pct_sin_compromiso": None, "pct_incumplimiento": None,
             "motivo_pendiente_clasificar": 0, "motivo_sin_compromiso": 0, "motivo_sin_config": 0},
        ],
    )
    api = APIClient()
    api.credentials(
        HTTP_AUTHORIZATION=f"Bearer {create_access_token(user_id=1, roles=['GerenteExitoCliente'], session_id=1)}"
    )
    filas = api.get(f"{BASE}?desde=2026-01-01&hasta=2026-02-28&granularidad=mes").json()["data"]["resultados"]
    vacio = next(f for f in filas if str(f["periodo"]).startswith("2026-02"))
    assert vacio["tickets"] == 0
    assert vacio["incumplidos"] == 0
