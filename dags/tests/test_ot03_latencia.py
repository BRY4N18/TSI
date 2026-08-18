"""T054 — un aviso ignorado no mejora la latencia."""

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

P1 = ID_PROSPECTO_PRUEBA + 70
P2 = ID_PROSPECTO_PRUEBA + 71


def _aviso(idn, idp, *, avance, segundos):
    return {
        "idnotificacion": idn,
        "fecha": FECHA_DE_PRUEBA,
        "fechahora": f"{FECHA_DE_PRUEBA} 10:00:00",
        "idprospecto": idp,
        "empresa": "Empresa prueba",
        "regla_disparada": "inactividad",
        "canal_aviso": "email",
        "hubo_avance": avance,
        "segundos_a_reaccion": segundos,
        "cargado_en": f"{FECHA_DE_PRUEBA} 12:00:00",
    }


@pytest.fixture
def escenario():
    asegurar_hechos_ventas_crm()
    limpiar_ventas_crm()
    insertar("dim_prospecto", [prospecto_de_prueba(P1), prospecto_de_prueba(P2)])
    insertar("hecho_notificacion_ventas", [
        _aviso(1, P1, avance=1, segundos=100),
        _aviso(2, P2, avance=0, segundos=None),
    ])
    yield
    limpiar_ventas_crm()


@requiere_modelo
class TestElAvisoIgnoradoNoMejoraLaLatencia:
    def test_queda_fuera_de_la_mediana(self, escenario):
        filas = ejecutar_ventas_crm("ot03_latencia_reaccion")
        assert filas, "sin filas no se puede ver la mediana"
        fila = filas[0]

        assert fila["avisos"] == 2
        assert fila["con_reaccion"] == 1
        assert fila["sin_reaccion"] == 1
        assert fila["segundos_mediana"] == 100, (
            "el aviso ignorado entro a la mediana: contado como cero, los "
            "peores casos mejorarian el indicador"
        )
