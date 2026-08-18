"""T009 — ampliar `dim_cliente` no rompe las cifras de Suscripciones (SC-009)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.almacen import ejecutar_suscripciones, requiere_modelo  # noqa: E402

from lib.clickhouse_http_client import query_clickhouse  # noqa: E402

COLUMNAS_CUENTAS = (
    "cohorte_alta",
    "fecha_baja",
    "motivo_baja",
    "etapa_onboarding_actual",
    "onboarding_completo",
    "resultado_solicitud",
)


@requiere_modelo
class TestLaAmpliacionNoRompeSuscripciones:
    @classmethod
    def setup_class(cls):
        from lib.ddl import ensure_columnas_nuevas_dimensiones, ensure_dim_cliente

        ensure_dim_cliente()
        ensure_columnas_nuevas_dimensiones()

    def test_las_seis_columnas_existen(self):
        nombres = {
            f["name"]
            for f in query_clickhouse(
                "SELECT name FROM system.columns "
                "WHERE database = currentDatabase() AND table = 'dim_cliente'"
            )
        }
        assert set(COLUMNAS_CUENTAS) <= nombres

    def test_mrr_sigue_sin_filas_de_ceros(self):
        assert ejecutar_suscripciones("ot06_mrr") == []

    def test_ingresos_siguen_sin_filas_de_ceros(self):
        assert ejecutar_suscripciones("ot06_ingresos") == []

    def test_distribucion_sigue_sin_filas_de_ceros(self):
        assert ejecutar_suscripciones("ot05_distribucion_cartera") == []
