"""T042 — la conversion por canal usa `desenlace`, nunca `activo`."""

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
    # Los dos serian `activo = false` en el origen. El modelo los separa.
    insertar("dim_prospecto", [
        prospecto_de_prueba(
            ID_PROSPECTO_PRUEBA + 60,
            canal="Web",
            etapa_actual="Ganado",
            desenlace="convertido",
        ),
        prospecto_de_prueba(
            ID_PROSPECTO_PRUEBA + 61,
            canal="Web",
            etapa_actual="Perdido",
            desenlace="perdido",
        ),
    ])
    yield
    limpiar_ventas_crm()


@requiere_modelo
class TestLaConversionUsaDesenlace:
    def test_el_perdido_no_cuenta_como_convertido(self, escenario):
        filas = ejecutar_ventas_crm("ot01_conversion_por_canal")
        web = next(f for f in filas if f["canal"] == "Web")

        assert web["prospectos"] == 2
        assert web["convertidos"] == 1, (
            "el perdido conto como convertido: el informe esta leyendo el "
            "estado de actividad, que los junta"
        )
        assert web["pct_conversion"] == 0.5
