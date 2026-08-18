"""T032 — churn por cohorte de alta, no por mes de baja (SC-002)."""

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
    insertar("dim_cliente", [
        cliente_de_prueba(
            ID_CLIENTE_PRUEBA,
            fecha_alta="2099-01-15 08:00:00",
            cohorte_alta="2099-01",
            fecha_baja="2099-06-10 12:00:00",
            motivo_baja=None,
            estado_comercial="dado de baja",
        ),
    ])
    yield
    limpiar_cuentas()


@requiere_modelo
class TestChurnPorCohorte:
    def test_la_baja_de_junio_cuenta_en_la_cohorte_de_enero(self, escenario):
        filas = ejecutar_cuentas(
            "ot17_churn_por_cohorte",
            desde="2099-06-01",
            hasta="2099-06-30",
        )
        assert filas, "el churn no devolvió filas"
        por = {f["cohorte_alta"]: f for f in filas}
        assert "2099-01" in por
        assert "2099-06" not in por
        assert int(por["2099-01"]["bajas"]) == 1
        assert int(por["2099-01"]["clientes_iniciales"]) == 1
        assert float(por["2099-01"]["pct_churn"]) == pytest.approx(1.0)
