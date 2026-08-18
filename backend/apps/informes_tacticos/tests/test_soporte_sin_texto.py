"""T079 — ninguna de las nueve respuestas contiene texto de ticket."""

from __future__ import annotations

import pytest
from rest_framework.test import APIClient

from apps.informes_tacticos.tests.test_soporte_openapi import RUTAS
from core.jwt_utils import create_access_token
from core.repositories.informes_tacticos.modelo_repository import ModeloRepository

BASE = "/api/v1/informes-tacticos/soporte"
TEXTO = ("asunto", "descripcion", "mensaje", "es_nota_interna", "nombre_agente")


@pytest.fixture(autouse=True)
def _pinot_en_memoria(mock_pinot, mock_kafka):
    return mock_pinot


@pytest.mark.parametrize("slug", list(RUTAS.values()))
def test_ninguna_respuesta_contiene_texto_de_ticket(slug, monkeypatch):
    monkeypatch.setattr(ModeloRepository, "ejecutar", lambda *a, **k: [])
    api = APIClient()
    api.credentials(
        HTTP_AUTHORIZATION=f"Bearer {create_access_token(user_id=1, roles=['GerenteExitoCliente'], session_id=1)}"
    )
    data = api.get(f"{BASE}/{slug}?desde=2026-01-01&hasta=2026-12-31").json()["data"]
    for fila in data.get("resultados", []):
        for campo in TEXTO:
            assert campo not in fila
    for item in data.get("declaraciones", []):
        assert "asunto" not in item
        assert "descripcion" not in item
        assert "es_nota_interna" not in item
        assert "nombre_agente" not in item
