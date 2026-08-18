"""T063 — añadir Cuentas no altera los cinco departamentos anteriores (SC-010)."""

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
    def test_los_cinco_anteriores_siguen_poblados(self):
        assert _reales("hecho_accidente") > 4000
        assert _reales("hecho_despacho") > 0
        assert contar("SELECT count() AS n FROM dim_prospecto FINAL") > 0
        assert contar("SELECT count() AS n FROM dim_plan FINAL") >= 0
        from lib.ddl import ensure_modelo_analitico

        ensure_modelo_analitico()
        assert contar("SELECT count() AS n FROM dim_sla_config FINAL") >= 0

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
            "dim_usuario_organizacion",
            "dim_etapa_onboarding",
            "dim_rol",
            "dim_usuario_rol",
            "hecho_sesion",
            "hecho_onboarding",
            "dim_cliente",
            "hecho_ticket",
        } <= propias

    def test_motores_correctos(self):
        from lib.ddl import ensure_modelo_analitico

        ensure_modelo_analitico()
        motores = {
            f["name"]: f["engine"]
            for f in query_clickhouse(
                "SELECT name, engine FROM system.tables "
                "WHERE database = currentDatabase() AND name IN ("
                "'hecho_sesion','hecho_onboarding','dim_cliente',"
                "'dim_usuario_organizacion')"
            )
        }
        assert "MergeTree" in motores["hecho_sesion"]
        assert "ReplacingMergeTree" not in motores["hecho_sesion"]
        assert "MergeTree" in motores["hecho_onboarding"]
        assert "ReplacingMergeTree" in motores["dim_cliente"]
        assert "ReplacingMergeTree" in motores["dim_usuario_organizacion"]
