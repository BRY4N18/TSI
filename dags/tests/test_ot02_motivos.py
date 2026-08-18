"""T034 — un motivo de pérdida ausente aparece como «sin motivo registrado»."""

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

PROSPECTO = ID_PROSPECTO_PRUEBA + 20


@pytest.fixture
def escenario():
    asegurar_hechos_ventas_crm()
    limpiar_ventas_crm()
    insertar("dim_prospecto", [
        prospecto_de_prueba(PROSPECTO, etapa_actual="Perdido", desenlace="perdido"),
    ])
    insertar("hecho_transicion_embudo", [
        {
            "idtransicion": 1,
            "fecha": FECHA_DE_PRUEBA,
            "fechahora": f"{FECHA_DE_PRUEBA} 10:00:00",
            "idprospecto": PROSPECTO,
            "empresa": "Empresa prueba",
            "canal": "Web",
            "tipo_organizacion": "Privada",
            "etapa_anterior": "Contactado",
            "etapa_nueva": "Perdido",
            "es_avance": 0,
            "es_terminal": 1,
            "motivo_perdida": None,
            "segundos_en_etapa_anterior": 100,
            "cargado_en": f"{FECHA_DE_PRUEBA} 12:00:00",
        }
    ])
    yield
    limpiar_ventas_crm()


@requiere_modelo
class TestMotivoAusenteNoSeDescarta:
    def test_aparece_como_sin_motivo_registrado(self, escenario):
        filas = ejecutar_ventas_crm("ot02_motivos_perdida")
        assert filas, "la perdida sin motivo se descarto"
        assert filas[0]["motivo"] == "sin motivo registrado"
        assert filas[0]["etapa_abandono"] == "Contactado"
        assert filas[0]["perdidos"] == 1
