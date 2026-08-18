"""T045–T046 — el embudo muestra la etapa que nadie completó (SC-004)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.almacen import (  # noqa: E402
    ID_CLIENTE_PRUEBA,
    ID_ONBOARDING_PRUEBA,
    asegurar_hechos_cuentas,
    cliente_de_prueba,
    etapas_catalogo,
    ejecutar_cuentas,
    insertar,
    limpiar_cuentas,
    onboarding_de_prueba,
    requiere_modelo,
)

from lib.dimensiones.dim_etapa_onboarding import CATALOGO  # noqa: E402


@pytest.fixture
def escenario():
    asegurar_hechos_cuentas()
    limpiar_cuentas()
    insertar("dim_etapa_onboarding", etapas_catalogo())
    insertar("dim_cliente", [cliente_de_prueba(ID_CLIENTE_PRUEBA, onboarding_completo=0)])
    insertar("hecho_onboarding", [
        onboarding_de_prueba(ID_ONBOARDING_PRUEBA, idetapa=1, etapa="cambio_password"),
        onboarding_de_prueba(
            ID_ONBOARDING_PRUEBA + 1, idetapa=2, etapa="perfil_corporativo",
        ),
        onboarding_de_prueba(
            ID_ONBOARDING_PRUEBA + 2, idetapa=3, etapa="preferencias",
        ),
    ])
    yield
    limpiar_cuentas()


@requiere_modelo
class TestEmbudoCatalogo:
    def test_la_etapa_fantasma_aparece_con_cero(self, escenario):
        filas = ejecutar_cuentas("ot04_embudo_abandono")
        etapas = [f["etapa"] for f in filas]
        assert etapas == [e[1] for e in CATALOGO]
        fantasma = next(f for f in filas if f["etapa"] == "verificacion_documental")
        assert int(fantasma["clientes_que_llegaron"]) == 0
        operativa = next(f for f in filas if f["etapa"] == "activacion_operativa")
        assert int(operativa["clientes_que_llegaron"]) == 0

    def test_el_orden_respeta_el_catalogo(self, escenario):
        filas = ejecutar_cuentas("ot04_embudo_abandono")
        assert [int(f["orden"]) for f in filas] == [e[0] for e in CATALOGO]
