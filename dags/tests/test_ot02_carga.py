"""T033 — la carga historica no se reescribe al reasignar (SC-005)."""

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

PROSPECTO = ID_PROSPECTO_PRUEBA + 10
ANTES = 7
AHORA = 8


def _asig(ida, ejecutivo, *, previo=None, fecha=FECHA_DE_PRUEBA, hora="09:00:00"):
    return {
        "idasignacion": ida,
        "fecha": fecha,
        "fechahora": f"{fecha} {hora}",
        "idprospecto": PROSPECTO,
        "empresa": "Empresa prueba",
        "idejecutivo": ejecutivo,
        "idejecutivo_previo": previo,
        "tipo_asignacion": "inicial" if previo is None else "reasignación",
        "motivo": None,
        "cargado_en": f"{FECHA_DE_PRUEBA} 12:00:00",
    }


@pytest.fixture
def escenario():
    asegurar_hechos_ventas_crm()
    limpiar_ventas_crm()
    insertar("dim_prospecto", [prospecto_de_prueba(PROSPECTO, valor_estimado=5000)])
    insertar("hecho_asignacion_prospecto", [_asig(1, ANTES)])
    yield
    limpiar_ventas_crm()


@requiere_modelo
class TestLaCargaHistoricaNoSeReescribe:
    def test_reasignar_despues_no_mueve_el_periodo_anterior(self, escenario):
        antes = ejecutar_ventas_crm("ot02_carga_por_ejecutivo")
        por_antes = {f["idejecutivo"]: f for f in antes}
        assert por_antes[ANTES]["activos"] == 1

        insertar("hecho_asignacion_prospecto", [
            _asig(2, AHORA, previo=ANTES, fecha="2099-12-15", hora="09:00:00"),
        ])

        despues = ejecutar_ventas_crm("ot02_carga_por_ejecutivo")
        por_despues = {f["idejecutivo"]: f for f in despues}

        assert por_despues[ANTES]["activos"] == 1, (
            "reasignar reescribio la carga del periodo anterior: el informe "
            "esta resolviendo el dueno al consultar contra el estado actual"
        )
        assert AHORA not in por_despues or por_despues[AHORA]["activos"] == 0
