"""T055 — «no hubo demos» no es «hubo demos y no se usaron» (SC-009)."""

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

PROSPECTO = ID_PROSPECTO_PRUEBA + 80


@pytest.fixture
def limpio():
    asegurar_hechos_ventas_crm()
    limpiar_ventas_crm()
    yield
    limpiar_ventas_crm()


@requiere_modelo
class TestNoHuboFrenteAHuboYNoSeUso:
    def test_sin_demos_devuelve_cero_filas(self, limpio):
        assert ejecutar_ventas_crm("ot03_intensidad_demo") == []

    def test_con_demo_sin_secciones_devuelve_fila_en_cero(self, limpio):
        insertar("dim_prospecto", [prospecto_de_prueba(PROSPECTO)])
        insertar("hecho_interaccion_demo", [
            {
                "idinteraccion": 1,
                "fecha": FECHA_DE_PRUEBA,
                "fechahora": f"{FECHA_DE_PRUEBA} 10:00:00",
                "idprospecto": PROSPECTO,
                "empresa": "Empresa prueba",
                "canal": "Web",
                "tipo_evento": "inicio_sesion",
                "seccion": None,
                "cargado_en": f"{FECHA_DE_PRUEBA} 12:00:00",
            }
        ])
        filas = ejecutar_ventas_crm("ot03_intensidad_demo")
        assert filas, (
            "hubo demo y no se uso, pero el informe devolvio vacio: eso se lee "
            "como «no hubo demos», la conclusion opuesta"
        )
        assert filas[0]["eventos"] >= 1
        assert filas[0]["secciones_distintas"] == 0
