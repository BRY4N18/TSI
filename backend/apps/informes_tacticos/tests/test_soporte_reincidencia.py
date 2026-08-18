"""T076, T077 — reincidencia: recuento, eje sustituido y sin identidad."""

from __future__ import annotations

import pytest
from rest_framework.test import APIClient

from core.jwt_utils import create_access_token
from core.repositories.informes_tacticos.modelo_repository import ModeloRepository

BASE = "/api/v1/informes-tacticos/soporte/reincidencia-clientes"


@pytest.fixture(autouse=True)
def _pinot_en_memoria(mock_pinot, mock_kafka):
    return mock_pinot


def test_cliente_con_tres_tickets_y_eje_sustituido(monkeypatch):
    monkeypatch.setattr(
        ModeloRepository,
        "ejecutar",
        lambda *a, **k: [{"id_cliente": 10, "tipo_cliente": "aseguradora",
                          "tickets": 3, "tipos_distintos": 2, "reaperturas": 1}],
    )
    api = APIClient()
    api.credentials(
        HTTP_AUTHORIZATION=f"Bearer {create_access_token(user_id=1, roles=['GerenteExitoCliente'], session_id=1)}"
    )
    data = api.get(f"{BASE}?desde=2026-01-01&hasta=2026-12-31").json()["data"]
    assert data["resultados"][0]["tickets"] == 3
    assert any(d["codigo"] == "servicio_no_registrado" for d in data["declaraciones"])


def test_trae_id_cliente_y_tipo_sin_mas_identidad(monkeypatch):
    monkeypatch.setattr(
        ModeloRepository,
        "ejecutar",
        lambda *a, **k: [{"id_cliente": 10, "tipo_cliente": "aseguradora",
                          "tickets": 3, "tipos_distintos": 1, "reaperturas": 0}],
    )
    api = APIClient()
    api.credentials(
        HTTP_AUTHORIZATION=f"Bearer {create_access_token(user_id=1, roles=['GerenteExitoCliente'], session_id=1)}"
    )
    cuerpo = api.get(f"{BASE}?desde=2026-01-01&hasta=2026-12-31").json()
    fila = cuerpo["data"]["resultados"][0]
    assert set(fila) <= {"id_cliente", "tipo_cliente", "tickets", "tipos_distintos", "reaperturas"}
    assert "nombre" not in fila
    assert "razon_social" not in fila
    assert "correo" not in fila
    assert "telefono" not in fila
