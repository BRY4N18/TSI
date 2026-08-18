"""T034 — sin sesión es ausencia de actividad, no cero días (SC-003)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.almacen import (  # noqa: E402
    ID_CLIENTE_PRUEBA,
    asegurar_hechos_cuentas,
    cliente_de_prueba,
    ejecutar_cuentas,
    insertar,
    limpiar_cuentas,
    requiere_modelo,
)


@pytest.fixture
def escenario():
    asegurar_hechos_cuentas()
    limpiar_cuentas()
    insertar("dim_cliente", [cliente_de_prueba(ID_CLIENTE_PRUEBA)])
    yield
    limpiar_cuentas()


@requiere_modelo
class TestCuentasEnRiesgo:
    def test_sin_sesion_no_es_cero_dias(self, escenario):
        filas = ejecutar_cuentas("ot17_cuentas_en_riesgo", dias_inactividad=90)
        assert filas, "un cliente sin sesiones debe aparecer en riesgo"
        fila = next(f for f in filas if int(f["idcliente"]) == ID_CLIENTE_PRUEBA)
        assert int(fila["sin_actividad_conocida"]) == 1
        assert fila["dias_sin_actividad"] is None
        assert fila["ultima_sesion"] is None
