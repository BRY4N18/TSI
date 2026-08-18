"""T056 — tickets por servicio: la fila «sin servicio» y su declaración."""

from __future__ import annotations

import pytest
from rest_framework.test import APIClient

from core.jwt_utils import create_access_token
from core.repositories.informes_tacticos.modelo_repository import ModeloRepository

BASE = "/api/v1/informes-tacticos/soporte/tickets-por-servicio"


@pytest.fixture(autouse=True)
def _pinot_en_memoria(mock_pinot, mock_kafka):
    return mock_pinot


def test_todos_nulos_devuelven_sin_servicio_y_la_declaracion(monkeypatch):
    monkeypatch.setattr(
        ModeloRepository,
        "ejecutar",
        lambda *a, **k: [{"id_servicio": None, "servicio": "sin servicio", "tickets": 14, "incumplidos": 8}],
    )
    api = APIClient()
    api.credentials(
        HTTP_AUTHORIZATION=f"Bearer {create_access_token(user_id=1, roles=['GerenteExitoCliente'], session_id=1)}"
    )
    data = api.get(f"{BASE}?desde=2026-01-01&hasta=2026-12-31").json()["data"]
    assert len(data["resultados"]) == 1
    assert data["resultados"][0]["servicio"] == "sin servicio"
    assert data["resultados"][0]["tickets"] == 14
    assert any(d["codigo"] == "servicio_no_registrado" for d in data["declaraciones"])
