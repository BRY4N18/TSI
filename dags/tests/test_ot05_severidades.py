"""T064 — una severidad habilitada y no usada aparece."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.almacen import (  # noqa: E402
    ID_PLAN_PRUEBA,
    ID_SUSCRIPCION_PRUEBA,
    asegurar_hechos_suscripciones,
    ejecutar_suscripciones,
    insertar,
    limpiar_suscripciones,
    plan_de_prueba,
    requiere_modelo,
    suscripcion_de_prueba,
)

import pytest


@pytest.fixture
def escenario():
    asegurar_hechos_suscripciones()
    limpiar_suscripciones()
    idplan = ID_PLAN_PRUEBA + 50
    insertar("dim_plan", [
        plan_de_prueba(idplan, nombre="Full", severidades=[1, 99]),
    ])
    insertar("hecho_suscripcion", [
        suscripcion_de_prueba(ID_SUSCRIPCION_PRUEBA + 50, plan="Full", idplan=idplan),
    ])
    yield
    limpiar_suscripciones()


@requiere_modelo
class TestSeveridades:
    def test_la_habilitada_sin_casos_aparece(self, escenario):
        filas = ejecutar_suscripciones("ot05_severidades_habilitadas_vs_usadas")
        assert filas
        ids = [str(f["severidad"]) for f in filas]
        assert any("99" in s for s in ids), ids
        sin_uso = [f for f in filas if int(f["casos_atendidos"] or 0) == 0]
        assert sin_uso, "una severidad habilitada y no usada debía aparecer"
        assert all(int(f["habilitada"]) == 1 for f in filas)
