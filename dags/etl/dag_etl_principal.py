"""DAG de referencia: patrón estándar extract/transform/load-parquet.

Este DAG NO es un informe de negocio -- es el ejemplo mínimo y completo del
patrón que deben seguir todos los DAGs `tactico` (ver
`specs/002-tactico/infraestructura/spec.md`): cada tarea recibe el contexto
de ejecución de Airflow, construye su ruta en `ETL/<fecha>/<hora>/` con
`lib/parquet_io.py`, y solo lee/escribe archivos parquet -- Airflow únicamente
orquesta el orden, no mueve ni transforma datos él mismo.

Escribe en la tabla `etl_demo_principal` (claramente separada de las tablas
de negocio) solo para demostrar el patrón end-to-end.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone

sys.path.insert(0, "/opt/airflow/dags")

import pandas as pd
from airflow import DAG
from airflow.operators.python import PythonOperator

from lib.clickhouse_http_client import execute_clickhouse, insert_rows
from lib.parquet_io import read_parquet, stage_path, write_parquet
from lib.pinot_http_client import query_pinot

DAG_ID = "etl_principal"


def _ensure_demo_table() -> None:
    execute_clickhouse(
        """
        CREATE TABLE IF NOT EXISTS etl_demo_principal (
            periodo String,
            total_accidentes UInt32,
            calculado_en DateTime
        ) ENGINE = MergeTree()
        ORDER BY periodo
        """
    )


def extract(**context) -> None:
    ts = context["ts"]
    rows = query_pinot(
        """
        SELECT DATETRUNC('day', fechahoraaccidente, 'MILLISECONDS') AS periodo,
               COUNT(*) AS total
        FROM Fact_Accidente
        GROUP BY periodo
        """
    )
    write_parquet(pd.DataFrame(rows), stage_path(ts, "extract"))


def transform(**context) -> None:
    ts = context["ts"]
    df = read_parquet(stage_path(ts, "extract"))

    if not df.empty:
        df["periodo"] = df["periodo"].apply(
            lambda epoch_ms: datetime.fromtimestamp(epoch_ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
        )
        df = df.rename(columns={"total": "total_accidentes"})
        df["calculado_en"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    write_parquet(df, stage_path(ts, "transform"))


def load(**context) -> None:
    ts = context["ts"]
    df = read_parquet(stage_path(ts, "transform"))
    if df.empty:
        return

    _ensure_demo_table()
    rows = df.to_dict("records")
    periodos = {r["periodo"] for r in rows}
    periodos_sql = ", ".join(f"'{p}'" for p in periodos)
    execute_clickhouse(f"ALTER TABLE etl_demo_principal DELETE WHERE periodo IN ({periodos_sql})")
    insert_rows("etl_demo_principal", rows)

    write_parquet(df, stage_path(ts, "load"))


with DAG(
    dag_id=DAG_ID,
    description="Referencia canónica del patrón extract/transform/load-parquet (no es un reporte de producción).",
    schedule="@daily",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    is_paused_upon_creation=True,
    tags=["etl", "referencia"],
) as dag:
    extract_task = PythonOperator(task_id="extract", python_callable=extract)
    transform_task = PythonOperator(task_id="transform", python_callable=transform)
    load_task = PythonOperator(task_id="load", python_callable=load)
    extract_task >> transform_task >> load_task
