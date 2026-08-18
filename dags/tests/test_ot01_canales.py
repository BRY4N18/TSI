"""T040 — los canales suman el total, con Desconocido incluido (SC-006)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.almacen import (  # noqa: E402
    ID_PROSPECTO_PRUEBA,
    asegurar_hechos_ventas_crm,
    ejecutar_ventas_crm,
    insertar,
    limpiar_ventas_crm,
    prospecto_de_prueba,
    requiere_modelo,
)


@pytest.fixture
def escenario():
    asegurar_hechos_ventas_crm()
    limpiar_ventas_crm()
    insertar("dim_prospecto", [
        prospecto_de_prueba(ID_PROSPECTO_PRUEBA + 40, canal="Web"),
        prospecto_de_prueba(ID_PROSPECTO_PRUEBA + 41, canal="Web"),
        prospecto_de_prueba(ID_PROSPECTO_PRUEBA + 42, canal="Desconocido"),
    ])
    yield
    limpiar_ventas_crm()


@requiere_modelo
class TestLosCanalesSumanElTotal:
    def test_desconocido_cuenta_y_la_suma_es_el_total(self, escenario):
        filas = ejecutar_ventas_crm("ot01_captacion_por_canal")
        por_canal = {f["canal"]: f for f in filas}

        assert "Desconocido" in por_canal, (
            "los prospectos sin canal se descartaron: los canales sumarian "
            "menos que el embudo"
        )
        assert sum(f["prospectos"] for f in filas) == 3
        assert por_canal["Desconocido"]["prospectos"] == 1
        assert por_canal["Web"]["prospectos"] == 2
        assert abs(sum(f["pct"] for f in filas) - 1) < 0.001
