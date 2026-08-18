"""T009 — los límites del plan quedan desplegados y son comparables."""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.dimensiones.dim_plan import construir, desplegar_limites  # noqa: E402


def test_despliega_unidades_usuarios_y_llamadas():
    limites = desplegar_limites(
        '{"unidades_max": 25, "usuarios_max": 10, "api_calls_mes": 10000, "api_calls_minuto": 60}'
    )
    assert limites["limite_unidades"] == 25
    assert limites["limite_usuarios"] == 10
    assert limites["limite_llamadas_mes"] == 10000
    assert limites["limite_llamadas_minuto"] == 60


def test_ausente_no_es_cero():
    limites = desplegar_limites("{}")
    assert limites["limite_unidades"] is None
    assert limites["limite_unidades"] != 0


def test_construir_deja_columnas_comparables():
    filas = construir(
        [{
            "idplan": 1,
            "nombre": "Pro",
            "precio": 99.0,
            "limites": '{"unidades_max": 5}',
            "nivel": "Profesional",
            "periodicidad": "Mensual",
            "severidades_desbloqueadas": "[1, 2]",
            "carga_lote_habilitada": False,
            "precio_excedente_llamada": -1.0,
            "activo": True,
        }],
        datetime(2026, 8, 17),
    )
    assert filas[0]["limite_unidades"] == 5
    assert filas[0]["severidades_habilitadas"] == [1, 2]
    assert filas[0]["precio_lista"] == 99.0
    assert filas[0]["precio_excedente_llamada"] is None
    assert "limites" not in filas[0]
