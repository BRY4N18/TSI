"""T063, T064 — tablero de cola con corte temporal y desglose por agente."""

from __future__ import annotations

import pytest
from rest_framework.test import APIClient

from core.jwt_utils import create_access_token
from core.repositories.informes_tacticos.modelo_repository import ModeloRepository

BASE = "/api/v1/informes-tacticos/soporte/tablero-cola"


@pytest.fixture(autouse=True)
def _pinot_en_memoria(mock_pinot, mock_kafka):
    return mock_pinot


def _cliente():
    api = APIClient()
    api.credentials(
        HTTP_AUTHORIZATION=f"Bearer {create_access_token(user_id=1, roles=['GerenteExitoCliente'], session_id=1)}"
    )
    return api


def test_el_tablero_acota_por_periodo_y_declara_la_diferencia(monkeypatch):
    capturado: dict = {}

    def fake(self, consulta, *, departamento, parametros):
        capturado.update(parametros)
        return [{"clave": "Abierto", "tickets": 3, "sin_agente": 1,
                 "sin_primera_respuesta": 2, "incumplidos": 1}]

    monkeypatch.setattr(ModeloRepository, "ejecutar", fake)
    data = _cliente().get(f"{BASE}?desde=2026-08-01&hasta=2026-08-31").json()["data"]
    assert capturado["sin_periodo"] == 0
    assert data["periodo"]["acotado"] is True
    assert any(d["codigo"] == "periodo_acotado_difiere_del_tablero" for d in data["declaraciones"])


def test_sin_periodo_no_acota(monkeypatch):
    capturado: dict = {}

    def fake(self, consulta, *, departamento, parametros):
        capturado.update(parametros)
        return [{"clave": "Abierto", "tickets": 14, "sin_agente": 0,
                 "sin_primera_respuesta": 4, "incumplidos": 8}]

    monkeypatch.setattr(ModeloRepository, "ejecutar", fake)
    data = _cliente().get(BASE).json()["data"]
    assert capturado["sin_periodo"] == 1
    assert data["periodo"]["acotado"] is False
    assert all(d["codigo"] != "periodo_acotado_difiere_del_tablero" for d in data["declaraciones"])


def test_tickets_sin_agente_aparecen_como_sin_asignar(monkeypatch):
    monkeypatch.setattr(
        ModeloRepository,
        "ejecutar",
        lambda *a, **k: [
            {"clave": "sin asignar", "tickets": 2, "sin_agente": 2,
             "sin_primera_respuesta": 2, "incumplidos": 0},
            {"clave": "7", "tickets": 5, "sin_agente": 0,
             "sin_primera_respuesta": 1, "incumplidos": 2},
        ],
    )
    data = _cliente().get(f"{BASE}?agrupar_por=agente").json()["data"]
    claves = {f["clave"] for f in data["resultados"]}
    assert "sin asignar" in claves
