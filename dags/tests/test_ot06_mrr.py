"""T038 — MRR: normaliza, excluye sin periodicidad, usa precio de suscripción (SC-003)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.base_propia import base_propia, vaciar  # noqa: E402,F401
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


@pytest.fixture
def escenario(base_propia):
    """⚠️ Corre sobre `base_propia`, no sobre el modelo cargado.

    Esta prueba compara su escenario contra un total **global** (el MRR, la
    utilización, el NRR). Contra el modelo real ese total incluye las
    suscripciones de verdad y el número esperado deja de tener sentido: pasaba
    solo mientras las tablas estaban vacías.
    """
    vaciar("hecho_suscripcion", "dim_plan")
    asegurar_hechos_suscripciones()
    limpiar_suscripciones()
    insertar("dim_plan", [plan_de_prueba(ID_PLAN_PRUEBA, precio_lista=999.0)])
    insertar("hecho_suscripcion", [
        suscripcion_de_prueba(
            ID_SUSCRIPCION_PRUEBA,
            precio=120.0,
            periodicidad="Mensual",
            precio_mensualizado=120.0,
        ),
        suscripcion_de_prueba(
            ID_SUSCRIPCION_PRUEBA + 1,
            idcliente=990001,
            precio=1200.0,
            periodicidad="Anual",
            precio_mensualizado=100.0,
        ),
        suscripcion_de_prueba(
            ID_SUSCRIPCION_PRUEBA + 2,
            idcliente=990002,
            precio=50.0,
            periodicidad=None,
            precio_mensualizado=None,
        ),
        suscripcion_de_prueba(
            ID_SUSCRIPCION_PRUEBA + 3,
            idcliente=990003,
            estado_derivado="cancelada",
            precio=80.0,
            precio_mensualizado=80.0,
            fecha_cancelacion="2099-12-01 09:00:00",
            motivo_cancelacion="baja",
        ),
    ])
    yield
    limpiar_suscripciones()


@requiere_modelo
class TestMrr:
    def test_normaliza_y_excluye_sin_periodicidad(self, escenario):
        filas = ejecutar_suscripciones("ot06_mrr")
        assert filas, "el MRR no devolvió filas"
        fila = filas[0]
        assert float(fila["mrr"]) == pytest.approx(220.0)
        assert int(fila["sin_periodicidad"]) == 1
        assert float(fila["mrr"]) != pytest.approx(270.0)

    def test_no_usa_el_precio_de_lista_del_plan(self, escenario):
        fila = ejecutar_suscripciones("ot06_mrr")[0]
        assert float(fila["mrr"]) != pytest.approx(999.0)
        assert float(fila["mrr"]) != pytest.approx(999.0 * 2)

    def test_los_cuatro_componentes_suman_el_neto(self, escenario):
        fila = ejecutar_suscripciones("ot06_mrr")[0]
        neto = (
            float(fila["nuevo"]) + float(fila["expansion"])
            - float(fila["contraccion"]) - float(fila["baja"])
        )
        assert neto == pytest.approx(float(fila["variacion_neta"]))

    def test_la_cancelada_no_entra_al_mrr(self, escenario):
        fila = ejecutar_suscripciones("ot06_mrr")[0]
        assert float(fila["mrr"]) == pytest.approx(220.0)
        assert float(fila["baja"]) == pytest.approx(80.0)
