"""T054 — adopción agrupa por (servicio, versión)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.almacen import (  # noqa: E402
    ID_LOG_PRUEBA,
    asegurar_hechos_partners,
    ejecutar_partners,
    insertar,
    llamada_de_prueba,
    limpiar_partners,
    requiere_modelo,
)


@pytest.fixture
def escenario():
    asegurar_hechos_partners()
    limpiar_partners()
    insertar("hecho_llamada_api", [
        llamada_de_prueba(ID_LOG_PRUEBA, servicio="datos", version_contrato="v1"),
        llamada_de_prueba(
            ID_LOG_PRUEBA + 1, servicio="despacho", version_contrato="v1",
            endpoint_path="/api/v1/despacho/unidades",
        ),
    ])
    yield
    limpiar_partners()


@requiere_modelo
def test_dos_servicios_con_v1_son_dos_filas(escenario):
    filas = ejecutar_partners("ot08_adopcion_versiones")
    claves = {(f["servicio"], f["version"]) for f in filas}
    assert ("datos", "v1") in claves
    assert ("despacho", "v1") in claves
    assert len(filas) == 2
    assert all(int(f["version_es_derivada"]) == 1 for f in filas)
