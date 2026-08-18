"""T060 — añadir Ventas y CRM no altera Emergencias ni Red Operativa (SC-010)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.almacen import contar, requiere_modelo  # noqa: E402

from lib.clickhouse_http_client import query_clickhouse  # noqa: E402

CASOS_EN_EL_ORIGEN = "SELECT COUNT(*) AS n FROM Fact_Accidente"
DESPACHOS_EN_EL_ORIGEN = "SELECT COUNT(*) AS n FROM Fact_Despacho"
PARTICION_DE_PRUEBA = 209912


def _reales(tabla: str) -> int:
    return contar(
        f"SELECT count() AS n FROM {tabla} FINAL "
        f"WHERE toYYYYMM(fecha) != {PARTICION_DE_PRUEBA}"
    )


@requiere_modelo
class TestElCrecimientoEsAditivo:
    def _origen(self, sql: str) -> int:
        from lib.pinot_http_client import query_pinot

        return query_pinot(sql)[0]["n"]

    def test_los_casos_siguen_cuadrando_con_el_origen(self):
        assert _reales("hecho_accidente") == self._origen(CASOS_EN_EL_ORIGEN)

    def test_los_despachos_siguen_cuadrando_con_el_origen(self):
        assert _reales("hecho_despacho") == self._origen(DESPACHOS_EN_EL_ORIGEN)

    def test_las_tablas_nuevas_existen_sin_compartir_almacen(self):
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
            "hecho_despacho",
            "dim_prospecto",
            "dim_canal",
            "hecho_transicion_embudo",
            "hecho_asignacion_prospecto",
            "hecho_interaccion_demo",
            "hecho_notificacion_ventas",
        } <= propias

    def test_los_hechos_nuevos_son_de_transaccion(self):
        from lib.ddl import ensure_modelo_analitico

        ensure_modelo_analitico()
        motores = {
            f["name"]: f["engine"]
            for f in query_clickhouse(
                "SELECT name, engine FROM system.tables "
                "WHERE database = currentDatabase() AND name LIKE 'hecho%'"
            )
        }
        for tabla in (
            "hecho_transicion_embudo",
            "hecho_asignacion_prospecto",
            "hecho_interaccion_demo",
            "hecho_notificacion_ventas",
        ):
            assert motores[tabla] == "MergeTree", tabla
