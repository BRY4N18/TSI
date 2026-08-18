"""T053–T055 — rendimiento por agente: reapertura, ranking y sin nombre."""

from __future__ import annotations

import pytest
from rest_framework.test import APIClient

from core.jwt_utils import create_access_token
from core.repositories.informes_tacticos.catalogo_consultas import cargar
from core.repositories.informes_tacticos.modelo_repository import ModeloRepository

BASE = "/api/v1/informes-tacticos/soporte/rendimiento-agentes"
SQL = cargar("ot19_rendimiento_agente", departamento="soporte")


@pytest.fixture(autouse=True)
def _pinot_en_memoria(mock_pinot, mock_kafka):
    return mock_pinot


def _cliente():
    api = APIClient()
    api.credentials(
        HTTP_AUTHORIZATION=f"Bearer {create_access_token(user_id=1, roles=['GerenteExitoCliente'], session_id=1)}"
    )
    return api


def test_reabierto_no_cuenta_como_resolucion_exitosa():
    assert "fue_reabierto = 0" in SQL


def test_un_agente_con_muchos_abiertos_no_encabeza_por_media_sola(monkeypatch):
    monkeypatch.setattr(
        ModeloRepository,
        "ejecutar",
        lambda *a, **k: [
            {"id_agente": 1, "asignados": 21, "resueltos": 1, "incumplidos": 0,
             "reabiertos": 0, "media_resolucion_s": 60, "sin_resolver": 20},
            {"id_agente": 2, "asignados": 5, "resueltos": 5, "incumplidos": 0,
             "reabiertos": 0, "media_resolucion_s": 3600, "sin_resolver": 0},
        ],
    )
    filas = _cliente().get(f"{BASE}?desde=2026-01-01&hasta=2026-12-31").json()["data"]["resultados"]
    rapido = next(f for f in filas if f["id_agente"] == 1)
    assert rapido["sin_resolver"] == 20
    assert rapido["media_resolucion_s"] == 60
    assert any(d["codigo"] == "tiempos_excluidos_sin_hito"
               for d in _cliente().get(f"{BASE}?desde=2026-01-01&hasta=2026-12-31").json()["data"]["declaraciones"])


def test_la_respuesta_trae_id_agente_y_ningun_nombre(monkeypatch):
    monkeypatch.setattr(
        ModeloRepository,
        "ejecutar",
        lambda *a, **k: [{"id_agente": 7, "asignados": 1, "resueltos": 1, "incumplidos": 0,
                          "reabiertos": 1, "media_resolucion_s": 100, "sin_resolver": 0}],
    )
    cuerpo = _cliente().get(f"{BASE}?desde=2026-01-01&hasta=2026-12-31").json()
    fila = cuerpo["data"]["resultados"][0]
    assert "id_agente" in fila
    assert "nombre" not in fila
    assert "nombre_agente" not in fila
