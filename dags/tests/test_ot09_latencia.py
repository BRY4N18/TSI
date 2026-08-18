"""T033 — p95 con media y muestras (SC-002, SC-011)."""

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
    requiere_modelo,
)


@pytest.fixture
def escenario():
    asegurar_hechos_partners()
    limpiar_partners()
    insertar("hecho_llamada_api", [
        llamada_de_prueba(ID_LOG_PRUEBA + i, latencia_ms=50 + i * 10)
        for i in range(5)
    ])
    yield
    limpiar_partners()


@requiere_modelo
class TestLatenciaP95:
    def test_devuelve_p95_media_y_muestras(self, escenario):
        filas = ejecutar_partners("ot09_latencia_p95", muestra_minima=20)
        assert filas
        fila = filas[0]
        assert "latencia_p95_ms" in fila and "latencia_media_ms" in fila
        assert float(fila["latencia_p95_ms"]) >= float(fila["latencia_media_ms"])
        assert int(fila["muestras"]) == 5
        assert int(fila["percentil_fiable"]) == 0
