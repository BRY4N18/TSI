"""T078–T082 — contrato OpenAPI, sin texto, solo lectura, FINAL y período vacío."""

from __future__ import annotations

from pathlib import Path

import pytest
from rest_framework.test import APIClient

from apps.informes_tacticos.services.soporte_compuestos_service import CATALOGO
from core.jwt_utils import create_access_token
from core.repositories.informes_tacticos.catalogo_consultas import cargar
from core.repositories.informes_tacticos.modelo_repository import ModeloRepository

BASE = "/api/v1/informes-tacticos/soporte"
TEXTO = ("asunto", "descripcion", "mensaje", "es_nota_interna", "nombre_agente")
OPENAPI = (
    Path(__file__).resolve().parents[4]
    / "specs" / "002-tactico" / "Soporte-Cliente" / "informes-compuestos-modelo"
    / "backend" / "contracts" / "informes-compuestos-soporte.openapi.yaml"
)

RUTAS = {
    "cumplimiento-sla": "cumplimiento-sla",
    "cumplimiento-sla-por-plan": "cumplimiento-sla/por-plan",
    "rendimiento-agentes": "rendimiento-agentes",
    "tickets-por-servicio": "tickets-por-servicio",
    "tablero-cola": "tablero-cola",
    "evolucion-incumplimiento": "evolucion-incumplimiento",
    "escalado-automatico": "escalado-automatico",
    "carga-entrante-resuelta": "carga-entrante-resuelta",
    "reincidencia-clientes": "reincidencia-clientes",
}


@pytest.fixture(autouse=True)
def _pinot_en_memoria(mock_pinot, mock_kafka):
    return mock_pinot


def _cliente():
    api = APIClient()
    api.credentials(
        HTTP_AUTHORIZATION=f"Bearer {create_access_token(user_id=1, roles=['GerenteExitoCliente'], session_id=1)}"
    )
    return api


@pytest.fixture
def _vacio(monkeypatch):
    monkeypatch.setattr(ModeloRepository, "ejecutar", lambda *a, **k: [])
    return _cliente()


@pytest.mark.parametrize("informe,slug", list(RUTAS.items()))
def test_los_nueve_responden_con_el_esquema(informe, slug, _vacio):
    assert OPENAPI.is_file()
    assert informe in CATALOGO
    respuesta = _vacio.get(f"{BASE}/{slug}?desde=2026-01-01&hasta=2026-12-31")
    assert respuesta.status_code == 200
    data = respuesta.json()["data"]
    assert "resultados" in data
    assert "declaraciones" in data
    assert isinstance(data["declaraciones"], list)


@pytest.mark.parametrize("slug", list(RUTAS.values()))
def test_ninguna_respuesta_contiene_texto_de_ticket(slug, _vacio):
    data = _vacio.get(f"{BASE}/{slug}?desde=2026-01-01&hasta=2026-12-31").json()["data"]
    for fila in data.get("resultados", []):
        for campo in TEXTO:
            assert campo not in fila
    for item in data.get("declaraciones", []):
        assert "asunto" not in item
        assert "descripcion" not in item
        assert "es_nota_interna" not in item
        assert "nombre_agente" not in item


@pytest.mark.parametrize("slug", list(RUTAS.values()))
@pytest.mark.parametrize("metodo", ["post", "put", "delete"])
def test_solo_lectura_devuelve_405(slug, metodo, _vacio):
    fn = getattr(_vacio, metodo)
    assert fn(f"{BASE}/{slug}").status_code == 405


def test_final_en_dimensiones_y_ticket_ausente_en_acciones():
    for nombre in CATALOGO.values():
        sql = cargar(nombre, departamento="soporte")
        if "hecho_ticket" in sql:
            assert "hecho_ticket" in sql and "FINAL" in sql
        if "hecho_accion_ticket" in sql:
            assert "hecho_accion_ticket AS a FINAL" not in sql
            assert "FROM hecho_accion_ticket FINAL" not in sql
        if "dim_servicio" in sql:
            assert "dim_servicio FINAL" in sql
        if "dim_plan" in sql:
            assert "dim_plan FINAL" in sql
        if "dim_cliente" in sql:
            assert "dim_cliente FINAL" in sql


@pytest.mark.parametrize("slug", list(RUTAS.values()))
def test_periodo_sin_datos_es_vacio_explicito_no_404(slug, _vacio):
    respuesta = _vacio.get(f"{BASE}/{slug}?desde=2026-01-01&hasta=2026-01-02")
    assert respuesta.status_code == 200
    data = respuesta.json()["data"]
    assert data["resultados"] == []
    assert any(d["codigo"] == "sin_datos_en_periodo" for d in data["declaraciones"])
