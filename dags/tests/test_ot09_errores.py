"""T034 — 429, 403 y 5xx no se suman (SC-005)."""

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
    filas = (
        [llamada_de_prueba(ID_LOG_PRUEBA + i, codigo_http=429) for i in range(3)]
        + [llamada_de_prueba(ID_LOG_PRUEBA + 10 + i, codigo_http=403) for i in range(2)]
        + [llamada_de_prueba(ID_LOG_PRUEBA + 20, codigo_http=500)]
    )
    insertar("hecho_llamada_api", filas)
    yield
    limpiar_partners()


@requiere_modelo
class TestTaxonomiaErrores:
    def test_las_tres_clases_van_separadas(self, escenario):
        filas = ejecutar_partners("ot09_taxonomia_errores")
        por = {f["clase_resultado"]: int(f["llamadas"]) for f in filas}
        assert por["limite_cupo"] == 3
        assert por["autorizacion"] == 2
        assert por["error_servicio"] == 1
        assert sum(por.values()) == 6
