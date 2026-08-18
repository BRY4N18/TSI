"""T036 — un partner sin llamadas aparece con cero, no omitido (SC-006)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.almacen import (  # noqa: E402
    ID_LOG_PRUEBA,
    ID_PARTNER_PRUEBA,
    asegurar_hechos_partners,
    ejecutar_partners,
    insertar,
    llamada_de_prueba,
    limpiar_partners,
    partner_de_prueba,
    requiere_modelo,
)


@pytest.fixture
def escenario():
    asegurar_hechos_partners()
    limpiar_partners()
    insertar("dim_partner", [
        partner_de_prueba(ID_PARTNER_PRUEBA, nombre="Con trafico"),
        partner_de_prueba(ID_PARTNER_PRUEBA + 1, nombre="Sin trafico"),
    ])
    insertar("hecho_llamada_api", [
        llamada_de_prueba(ID_LOG_PRUEBA, idpartner=ID_PARTNER_PRUEBA, partner="Con trafico"),
    ])
    yield
    limpiar_partners()


@requiere_modelo
def test_el_partner_sin_llamadas_aparece_con_cero(escenario):
    filas = ejecutar_partners("ot09_comparativa_partners")
    por = {f["partner"]: int(f["llamadas"]) for f in filas}
    assert por["Con trafico"] == 1
    assert por["Sin trafico"] == 0
