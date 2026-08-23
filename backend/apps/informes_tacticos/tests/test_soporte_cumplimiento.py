"""T048–T052 — cumplimiento BSC: SLA histórico, cobertura y denominador ausente."""

from __future__ import annotations

import re

import pytest
from rest_framework.test import APIClient

from core.jwt_utils import create_access_token
from core.repositories.informes_tacticos.catalogo_consultas import cargar
from core.repositories.informes_tacticos.modelo_repository import ModeloRepository

BASE = "/api/v1/informes-tacticos/soporte/cumplimiento-sla"
SQL = cargar("ot19_cumplimiento_sla", departamento="soporte")


@pytest.fixture(autouse=True)
def _pinot_en_memoria(mock_pinot, mock_kafka):
    return mock_pinot


def _cliente():
    api = APIClient()
    api.credentials(
        HTTP_AUTHORIZATION=f"Bearer {create_access_token(user_id=1, roles=['GerenteExitoCliente'], session_id=1)}"
    )
    return api


def _fila(**extra):
    fila = {
        "periodo": "2026-05-01", "tickets": 2, "con_compromiso": 1, "sin_compromiso": 1,
        "cumplidos": 1, "incumplidos": 0, "pct_cumplimiento": 100.0,
        "pct_sin_compromiso": 50.0, "motivo_pendiente_clasificar": 1,
        "motivo_sin_compromiso": 0, "motivo_sin_config": 0,
    }
    fila.update(extra)
    return fila


def test_la_consulta_no_une_el_sla_vigente_hoy():
    assert "es_vigente" not in SQL
    assert "dim_sla_config" not in SQL
    # Lee el hecho directamente y con `FINAL`. Se comprueba por partes y no como
    # cadena literal porque la tabla lleva alias (`FROM hecho_ticket AS t FINAL`):
    # el alias es obligatorio para poder calificar `t.motivo_sin_compromiso`, sin
    # lo cual ClickHouse rechaza la consulta con ILLEGAL_AGGREGATION. Lo que esta
    # prueba protege es que no se una el SLA vigente hoy, no cómo se nombra la
    # tabla — y atarla a la forma exacta la hacía fallar por un cambio inocuo.
    assert re.search(r"FROM hecho_ticket(?: AS \w+)? FINAL", SQL)
    assert "pct_sin_compromiso" in SQL
    assert "nullIf" in SQL


def test_ticket_de_5h_antes_del_cambio_sale_cumplido(monkeypatch):
    """Resuelto en 5 h con límite 86400: cumplido. Contra 7200 actuales, no."""
    monkeypatch.setattr(ModeloRepository, "ejecutar", lambda *a, **k: [_fila()])
    data = _cliente().get(f"{BASE}?desde=2026-05-01&hasta=2026-05-31").json()["data"]
    assert data["resultados"][0]["pct_cumplimiento"] == 100.0
    assert data["resultados"][0]["cumplidos"] == 1
    assert any(d["codigo"] == "sla_historico_aplicado" for d in data["declaraciones"])


def test_un_ticket_sin_sla_no_cuenta_como_incumplido(monkeypatch):
    monkeypatch.setattr(
        ModeloRepository,
        "ejecutar",
        lambda *a, **k: [_fila(
            tickets=1, con_compromiso=0, sin_compromiso=1, cumplidos=0,
            incumplidos=0, pct_cumplimiento=None, pct_sin_compromiso=100.0,
        )],
    )
    fila = _cliente().get(f"{BASE}?desde=2026-05-01&hasta=2026-05-31").json()["data"]["resultados"][0]
    assert fila["incumplidos"] == 0
    assert fila["sin_compromiso"] == 1
    assert fila["pct_cumplimiento"] is None


def test_periodo_sin_compromiso_devuelve_pct_ausente(monkeypatch):
    monkeypatch.setattr(
        ModeloRepository,
        "ejecutar",
        lambda *a, **k: [_fila(
            con_compromiso=0, sin_compromiso=3, tickets=3, cumplidos=0,
            incumplidos=0, pct_cumplimiento=None, pct_sin_compromiso=100.0,
        )],
    )
    fila = _cliente().get(f"{BASE}?desde=2026-05-01&hasta=2026-05-31").json()["data"]["resultados"][0]
    assert fila["pct_cumplimiento"] is None
    assert fila["pct_cumplimiento"] != 0


def test_dejar_sin_clasificar_sube_cumplimiento_y_cobertura():
    def _pct(tickets):
        con = sum(1 for t in tickets if t["tiene_compromiso"])
        sin = len(tickets) - con
        cumplidos = sum(1 for t in tickets if t["desenlace"] == "cumplido")
        pct = None if con == 0 else round(100.0 * cumplidos / con, 2)
        pct_sin = round(100.0 * sin / len(tickets), 2)
        return pct, pct_sin

    base = [
        {"tiene_compromiso": 1, "desenlace": "cumplido"},
        {"tiene_compromiso": 1, "desenlace": "incumplido"},
    ]
    antes = _pct(base)
    # Dejar el incumplido sin clasificar: sube el cumplimiento y el % sin compromiso.
    despues = _pct([
        {"tiene_compromiso": 1, "desenlace": "cumplido"},
        {"tiene_compromiso": 0, "desenlace": None},
    ])
    assert despues[0] > antes[0]
    assert despues[1] > antes[1]


def test_los_tres_motivos_salen_separados(monkeypatch):
    monkeypatch.setattr(
        ModeloRepository,
        "ejecutar",
        lambda *a, **k: [_fila(
            motivo_pendiente_clasificar=3, motivo_sin_compromiso=1, motivo_sin_config=2,
            sin_compromiso=6, tickets=14, con_compromiso=8,
        )],
    )
    fila = _cliente().get(f"{BASE}?desde=2026-01-01&hasta=2026-12-31").json()["data"]["resultados"][0]
    motivos = fila["sin_compromiso_por_motivo"]
    assert motivos == {
        "pendiente_clasificar": 3,
        "sin_compromiso": 1,
        "sin_configuracion": 2,
    }
    assert "sin_compromiso_total" not in fila
