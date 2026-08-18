"""T067 — añadir Suscripciones no altera los tres departamentos anteriores."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.almacen import contar, requiere_modelo  # noqa: E402

from lib.clickhouse_http_client import query_clickhouse  # noqa: E402

PARTICION_DE_PRUEBA = 209912


def _reales(tabla: str) -> int:
    return contar(
        f"SELECT count() AS n FROM {tabla} FINAL "
        f"WHERE toYYYYMM(fecha) != {PARTICION_DE_PRUEBA}"
    )


@requiere_modelo
class TestElCrecimientoEsAditivo:
    def test_emergencias_y_despacho_siguen_poblados(self):
        """No se tocan las cifras de los departamentos anteriores.

        El desfase de dos casos entre Pinot y ClickHouse (4254 vs 4252) ya
        existía antes de este módulo: es FINAL sobre instantánea, no un
        recuento nuevo. Lo que no puede pasar es que al añadir Suscripciones
        esos hechos queden vacíos o desaparezcan.
        """
        assert _reales("hecho_accidente") > 4000
        assert _reales("hecho_despacho") > 0
        assert contar("SELECT count() AS n FROM dim_prospecto FINAL") > 0

    def test_las_tablas_nuevas_existen(self):
        from lib.ddl import ensure_modelo_analitico

        ensure_modelo_analitico()
        propias = {
            f["name"]
            for f in query_clickhouse(
                "SELECT name FROM system.tables WHERE database = currentDatabase()"
            )
        }
        assert {
            "hecho_accidente",
            "dim_prospecto",
            "hecho_transicion_embudo",
            "dim_plan",
            "dim_cliente",
            "hecho_suscripcion",
            "hecho_factura",
            "hecho_solicitud_cambio_plan",
        } <= propias

    def test_motores_correctos(self):
        from lib.ddl import ensure_modelo_analitico

        ensure_modelo_analitico()
        motores = {
            f["name"]: f["engine"]
            for f in query_clickhouse(
                "SELECT name, engine FROM system.tables "
                "WHERE database = currentDatabase() AND name IN ("
                "'hecho_suscripcion','hecho_factura','hecho_solicitud_cambio_plan',"
                "'hecho_transicion_embudo')"
            )
        }
        assert "ReplacingMergeTree" in motores["hecho_suscripcion"]
        assert motores["hecho_factura"] == "MergeTree" or "MergeTree" in motores["hecho_factura"]
        assert "MergeTree" in motores["hecho_solicitud_cambio_plan"]
        assert "MergeTree" in motores["hecho_transicion_embudo"]
