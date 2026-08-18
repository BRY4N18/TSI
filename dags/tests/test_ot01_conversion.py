"""T041 — un canal sin prospectos devuelve sin dato, no 0 %."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.almacen import (  # noqa: E402
    FECHA_DE_PRUEBA,
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
    insertar("dim_canal", [
        {
            "idcanal": ID_PROSPECTO_PRUEBA + 1,
            "canal": "Feria inexistente",
            "version": f"{FECHA_DE_PRUEBA} 12:00:00",
        }
    ])
    insertar("dim_prospecto", [
        prospecto_de_prueba(ID_PROSPECTO_PRUEBA + 50, canal="Web"),
    ])
    yield
    limpiar_ventas_crm()


@requiere_modelo
class TestCanalSinProspectosEsSinDato:
    def test_no_aparece_con_cero_por_ciento(self, escenario):
        filas = ejecutar_ventas_crm("ot01_conversion_por_canal")
        canales = {f["canal"] for f in filas}

        assert "Feria inexistente" not in canales, (
            "un canal sin prospectos aparecio con 0 %: eso afirma que se midio "
            "y nadie convirtio. Sin dato es no aparecer."
        )
        assert "Web" in canales
        web = next(f for f in filas if f["canal"] == "Web")
        assert web["pct_conversion"] is not None or web["prospectos"] > 0
