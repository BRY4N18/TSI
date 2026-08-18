"""T030 — el prospecto estancado es el más lento, no el más rápido (SC-004).

Si la consulta solo midiera etapas ya abandonadas, quien lleva semanas sin
moverse no aparecería — o peor, no tendría duracion y el informe lo presentaria
como el mas rapido. El tramo abierto existe para encontrarlo.
"""

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

ESTANCADO = ID_PROSPECTO_PRUEBA + 1
MOVIDO = ID_PROSPECTO_PRUEBA + 2


@pytest.fixture
def escenario():
    asegurar_hechos_ventas_crm()
    limpiar_ventas_crm()
    insertar("dim_prospecto", [
        prospecto_de_prueba(
            ESTANCADO,
            etapa_actual="Nuevo",
            fecha_registro="2099-11-10 08:00:00",
        ),
        prospecto_de_prueba(MOVIDO, etapa_actual="Contactado"),
    ])
    insertar("hecho_transicion_embudo", [
        {
            "idtransicion": 1,
            "fecha": FECHA_DE_PRUEBA,
            "fechahora": f"{FECHA_DE_PRUEBA} 10:00:00",
            "idprospecto": MOVIDO,
            "empresa": "Empresa prueba",
            "canal": "Web",
            "tipo_organizacion": "Privada",
            "etapa_anterior": "Nuevo",
            "etapa_nueva": "Contactado",
            "es_avance": 1,
            "es_terminal": 0,
            "motivo_perdida": None,
            "segundos_en_etapa_anterior": 3600,
            "cargado_en": f"{FECHA_DE_PRUEBA} 12:00:00",
        }
    ])
    yield
    limpiar_ventas_crm()


@requiere_modelo
class TestElEstancadoEsElMasLento:
    def test_aparece_con_la_permanencia_mayor_y_en_abiertos(self, escenario):
        filas = {f["etapa"]: f for f in ejecutar_ventas_crm("ot02_permanencia_por_etapa")}

        assert "Nuevo" in filas, (
            "el estancado no aparece: la consulta solo mide etapas abandonadas "
            "y deja fuera a quienes el informe existe para encontrar"
        )
        assert filas["Nuevo"]["abiertos"] >= 1
        assert filas["Nuevo"]["segundos_mediana"] > 3600
