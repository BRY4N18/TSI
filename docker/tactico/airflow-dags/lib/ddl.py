"""DDL idempotente de las 3 tablas de informes tácticos compuestos (data-model.md).

Cada DAG llama a su `ensure_*_table()` al inicio de su corrida — `CREATE TABLE
IF NOT EXISTS` es seguro de repetir (idempotente a nivel de esquema).
"""

from __future__ import annotations

from lib.clickhouse_http_client import execute_clickhouse


def ensure_perdida_senal_table() -> None:
    execute_clickhouse(
        """
        CREATE TABLE IF NOT EXISTS perdida_senal_gps (
            periodo Date,
            idunidademergencia Int32,
            idaccidente String,
            inicio_hueco DateTime,
            fin_hueco DateTime,
            duracion_seg Int32,
            umbral_usado_seg Int32,
            calculado_en DateTime
        ) ENGINE = MergeTree()
        ORDER BY (periodo, idunidademergencia, inicio_hueco)
        """
    )


def ensure_indice_calidad_table() -> None:
    execute_clickhouse(
        """
        CREATE TABLE IF NOT EXISTS indice_calidad_historico (
            periodo Date,
            pct_completitud Float64,
            pct_descarte Float64,
            pct_fusion Float64,
            pct_cobertura_evidencia Float64,
            indice_consolidado Float64,
            calculado_en DateTime
        ) ENGINE = MergeTree()
        ORDER BY periodo
        """
    )


def ensure_rendimiento_proveedor_table() -> None:
    execute_clickhouse(
        """
        CREATE TABLE IF NOT EXISTS rendimiento_por_proveedor (
            periodo Date,
            idcliente Int32,
            pct_rechazo Float64,
            tiempo_llegada_promedio_seg Float64,
            pct_abortos Float64,
            total_despachos Int32,
            calculado_en DateTime
        ) ENGINE = MergeTree()
        ORDER BY (periodo, idcliente)
        """
    )
