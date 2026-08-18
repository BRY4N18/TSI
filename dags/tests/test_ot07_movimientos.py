"""T054 — el tipo de movimiento sale del delta de precio, no del nivel."""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.hechos.hecho_solicitud_cambio_plan import construir, tipo_movimiento  # noqa: E402
from tests.almacen import (  # noqa: E402
    asegurar_hechos_suscripciones,
    ejecutar_suscripciones,
    insertar,
    limpiar_suscripciones,
    requiere_modelo,
    solicitud_de_prueba,
)

import pytest


def test_subir_de_nivel_a_un_plan_mas_barato_es_downgrade():
    assert tipo_movimiento(-20.0) == "downgrade"
    assert tipo_movimiento(20.0) == "upgrade"
    assert tipo_movimiento(0.0) == "lateral"


def test_construir_usa_el_precio_no_el_nivel():
    filas = construir(
        {
            "solicitudes": [{
                "idsolicitud": 1,
                "idcliente": 1,
                "idplanactual": 1,
                "idplansolicitado": 2,
                "estado": "Aprobada",
                "fecha_solicitud": 1786622400000,
                "fecha_resolucion": 1786626000000,
            }],
            "dim_plan": [
                {"idplan": 1, "nombre": "Profesional", "precio_lista": 200},
                {"idplan": 2, "nombre": "Empresarial", "precio_lista": 80},
            ],
        },
        datetime(2026, 8, 17, 12, 0, 0),
    )
    assert filas[0]["tipo_movimiento"] == "downgrade"
    assert filas[0]["delta_precio"] == -120.0


@pytest.fixture
def escenario():
    asegurar_hechos_suscripciones()
    limpiar_suscripciones()
    insertar("hecho_solicitud_cambio_plan", [
        solicitud_de_prueba(
            990010,
            tipo_movimiento="downgrade",
            delta_precio=-40.0,
            plan_actual="Profesional",
            plan_solicitado="Empresarial",
        ),
    ])
    yield
    limpiar_suscripciones()


@requiere_modelo
def test_el_informe_publica_downgrade(escenario):
    filas = ejecutar_suscripciones("ot07_movimientos_plan")
    tipos = {f["tipo_movimiento"] for f in filas}
    assert "downgrade" in tipos
