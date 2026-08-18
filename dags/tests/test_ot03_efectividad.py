"""T056 — efectividad de la nutrición: dos grupos, cada uno con su denominador."""

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

CON_DEMO = ID_PROSPECTO_PRUEBA + 90
SIN_DEMO = ID_PROSPECTO_PRUEBA + 91


@pytest.fixture
def escenario():
    asegurar_hechos_ventas_crm()
    limpiar_ventas_crm()
    insertar("dim_prospecto", [
        prospecto_de_prueba(CON_DEMO, desenlace="convertido", etapa_actual="Ganado"),
        prospecto_de_prueba(SIN_DEMO, desenlace="en_curso"),
    ])
    insertar("hecho_interaccion_demo", [
        {
            "idinteraccion": 1,
            "fecha": FECHA_DE_PRUEBA,
            "fechahora": f"{FECHA_DE_PRUEBA} 10:00:00",
            "idprospecto": CON_DEMO,
            "empresa": "Empresa prueba",
            "canal": "Web",
            "tipo_evento": "visita",
            "seccion": "planes",
            "cargado_en": f"{FECHA_DE_PRUEBA} 12:00:00",
        }
    ])
    yield
    limpiar_ventas_crm()


@requiere_modelo
class TestEfectividadDosGrupos:
    def test_dos_filas_cada_una_con_su_denominador(self, escenario):
        filas = {f["grupo"]: f for f in ejecutar_ventas_crm("ot03_efectividad_nutricion")}

        assert set(filas) == {"con_demo", "sin_demo"}
        assert filas["con_demo"]["denominador"] == 1
        assert filas["sin_demo"]["denominador"] == 1
        assert filas["con_demo"]["convertidos"] == 1
        assert filas["sin_demo"]["convertidos"] == 0
        assert filas["con_demo"]["pct_conversion"] == 1
        assert filas["sin_demo"]["pct_conversion"] == 0
