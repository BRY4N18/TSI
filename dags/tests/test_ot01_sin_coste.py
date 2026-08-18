"""T039 — el informe de convertidos no trae coste, ni siquiera nulo (FR-022)."""

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

PROHIBIDAS = ("coste", "importe", "inversion", "cac")


@pytest.fixture
def escenario():
    asegurar_hechos_ventas_crm()
    limpiar_ventas_crm()
    insertar("dim_prospecto", [
        prospecto_de_prueba(
            ID_PROSPECTO_PRUEBA + 30,
            canal="Web",
            desenlace="convertido",
            etapa_actual="Ganado",
        ),
    ])
    yield
    limpiar_ventas_crm()


@requiere_modelo
class TestConvertidosSinCoste:
    def test_ninguna_clave_de_coste_ni_nula(self, escenario):
        filas = ejecutar_ventas_crm("ot01_convertidos_por_canal")
        assert filas, "sin filas esta comprobacion no mira ninguna clave"
        for fila in filas:
            for clave in fila:
                bajo = clave.lower()
                for prohibida in PROHIBIDAS:
                    assert prohibida not in bajo, (
                        f"aparece '{clave}': una columna de coste, aunque vacia, "
                        f"invita a rellenarla desde fuera"
                    )
            assert "nota_indicador" in fila
            assert "CAC" in fila["nota_indicador"] or "cac" in fila["nota_indicador"].lower()
