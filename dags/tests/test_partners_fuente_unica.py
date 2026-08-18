"""T019 — una sola fuente de consumo: no hay tabla preagregada (SC-012)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.almacen import requiere_modelo  # noqa: E402

from lib.clickhouse_http_client import query_clickhouse  # noqa: E402
from lib.hechos.hecho_llamada_api import CONSULTA_LLAMADAS  # noqa: E402


@requiere_modelo
def test_no_existe_tabla_de_consumo_preagregado():
    from lib.ddl import ensure_modelo_analitico

    ensure_modelo_analitico()
    filas = query_clickhouse(
        "SELECT name FROM system.tables "
        "WHERE database = currentDatabase() AND name ILIKE '%integracion%'"
    )
    assert filas == [], f"apareció una tabla preagregada: {filas}"


def test_el_hecho_no_consulta_la_preagregada():
    assert "Fact_APIIntegracion" not in CONSULTA_LLAMADAS
    assert "hecho_api_integracion" not in CONSULTA_LLAMADAS.lower()
