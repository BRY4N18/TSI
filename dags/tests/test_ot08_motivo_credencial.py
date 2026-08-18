"""T051 — cuatro motivos de inactividad (SC-003)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.almacen import (  # noqa: E402
    ID_CREDENCIAL_PRUEBA,
    ID_PARTNER_PRUEBA,
    asegurar_hechos_partners,
    credencial_de_prueba,
    ejecutar_partners,
    insertar,
    limpiar_partners,
    partner_de_prueba,
    requiere_modelo,
)


@pytest.fixture
def escenario():
    asegurar_hechos_partners()
    limpiar_partners()
    insertar("dim_partner", [partner_de_prueba(ID_PARTNER_PRUEBA)])
    insertar("dim_credencial_api", [
        credencial_de_prueba(ID_CREDENCIAL_PRUEBA, motivo="revocada"),
        credencial_de_prueba(ID_CREDENCIAL_PRUEBA + 1, motivo="expirada"),
        credencial_de_prueba(ID_CREDENCIAL_PRUEBA + 2, motivo="cascada"),
        credencial_de_prueba(ID_CREDENCIAL_PRUEBA + 3, motivo="suspension_manual"),
    ])
    yield
    limpiar_partners()


@requiere_modelo
def test_revocada_y_caducada_no_se_mezclan(escenario):
    filas = ejecutar_partners("ot08_motivo_credencial_inactiva")
    motivos = {f["motivo_inactividad"] for f in filas}
    assert "revocada" in motivos
    assert "expirada" in motivos
    assert "cascada" in motivos
    assert "suspension_manual" in motivos
