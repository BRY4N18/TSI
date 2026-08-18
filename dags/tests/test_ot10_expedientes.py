"""T060 — portal y API se separan como canales."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.almacen import (  # noqa: E402
    FECHA_DE_PRUEBA,
    ID_CLIENTE_PRUEBA,
    ID_LOG_PRUEBA,
    asegurar_hechos_partners,
    ejecutar_partners,
    insertar,
    llamada_de_prueba,
    limpiar_partners,
    requiere_modelo,
)


def _accidente():
    return {
        "idaccidente": "P-TEST-1",
        "fecha": FECHA_DE_PRUEBA,
        "fechahora_accidente": f"{FECHA_DE_PRUEBA} 10:00:00",
        "franja_horaria": "manana",
        "fue_descartado": 0,
        "es_duplicado": 0,
        "cargado_en": f"{FECHA_DE_PRUEBA} 12:00:00",
        "version": f"{FECHA_DE_PRUEBA} 12:00:00",
    }


@pytest.fixture
def escenario():
    asegurar_hechos_partners()
    limpiar_partners()
    insertar("hecho_accidente", [_accidente()])
    insertar("hecho_llamada_api", [
        llamada_de_prueba(ID_LOG_PRUEBA, idcliente=ID_CLIENTE_PRUEBA),
    ])
    yield
    limpiar_partners()
    from lib.clickhouse_http_client import execute_clickhouse
    from tests.almacen import PARTICION_DE_PRUEBA

    execute_clickhouse(f"ALTER TABLE hecho_accidente DROP PARTITION {PARTICION_DE_PRUEBA}")


@requiere_modelo
def test_los_dos_canales_aparecen(escenario):
    filas = ejecutar_partners("ot10_volumen_expedientes")
    canales = {f["canal"] for f in filas}
    assert "portal" in canales
    assert "api" in canales
