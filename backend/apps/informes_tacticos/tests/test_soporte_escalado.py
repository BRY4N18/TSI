"""T065, T066 — escalado automático y humano en columnas distintas."""

from __future__ import annotations

import pytest
from rest_framework.test import APIClient

from core.jwt_utils import create_access_token
from core.repositories.informes_tacticos.catalogo_consultas import cargar
from core.repositories.informes_tacticos.modelo_repository import ModeloRepository

BASE = "/api/v1/informes-tacticos/soporte/escalado-automatico"
SQL = cargar("ot20_tasa_escalado_automatico", departamento="soporte")


@pytest.fixture(autouse=True)
def _pinot_en_memoria(mock_pinot, mock_kafka):
    return mock_pinot


def test_la_consulta_usa_uniqexact_y_no_final_en_acciones():
    assert "uniqExact" in SQL
    assert "hecho_accion_ticket AS a" in SQL
    assert "hecho_accion_ticket AS a FINAL" not in SQL
    assert "a FINAL" not in SQL.replace("hecho_ticket AS t FINAL", "")


def test_automatico_y_humano_no_se_suman(monkeypatch):
    monkeypatch.setattr(
        ModeloRepository,
        "ejecutar",
        lambda *a, **k: [{
            "tipo_incidencia": "tecnica", "prioridad": "alta", "tickets": 7,
            "con_escalado_automatico": 5, "con_escalado_humano": 2,
            "pct_escalado_automatico": 71.43,
        }],
    )
    api = APIClient()
    api.credentials(
        HTTP_AUTHORIZATION=f"Bearer {create_access_token(user_id=1, roles=['GerenteExitoCliente'], session_id=1)}"
    )
    fila = api.get(f"{BASE}?desde=2026-01-01&hasta=2026-12-31").json()["data"]["resultados"][0]
    assert "con_escalado_automatico" in fila
    assert "con_escalado_humano" in fila
    assert "con_escalado" not in fila
    assert "total_escalados" not in fila


def test_tres_escalados_del_mismo_ticket_cuentan_como_uno():
    assert "uniqExactIf(a.id_reclamo" in SQL
