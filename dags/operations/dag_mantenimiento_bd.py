"""DAG: mantenimiento periódico de las tablas ClickHouse del stack `tactico`.

Ejecuta `OPTIMIZE TABLE` sobre las tablas gestionadas por los DAGs de
negocio (compactan las partes de MergeTree acumuladas por los `ALTER ...
DELETE` + `INSERT` de cada corrida diaria). No toca esquema ni datos.
"""

from __future__ import annotations

import sys
from datetime import datetime

sys.path.insert(0, "/opt/airflow/dags")

from airflow import DAG
from airflow.operators.python import PythonOperator

from lib.clickhouse_http_client import execute_clickhouse

DAG_ID = "mantenimiento_bd"

TABLAS_GESTIONADAS = [
    "perdida_senal_gps",
    "indice_calidad_historico",
    "rendimiento_por_proveedor",
    "etl_demo_principal",
]


def optimizar(**context) -> None:
    for tabla in TABLAS_GESTIONADAS:
        execute_clickhouse(f"OPTIMIZE TABLE {tabla} FINAL")


with DAG(
    dag_id=DAG_ID,
    description="OPTIMIZE TABLE sobre las tablas ClickHouse gestionadas por los DAGs tácticos.",
    schedule="@weekly",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    is_paused_upon_creation=True,
    tags=["operations", "tactico"],
) as dag:
    optimizar_task = PythonOperator(task_id="optimizar", python_callable=optimizar)
