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

# ⚠️ **Repuntado al modelo el 2026-08-15** (decisión #20, opción B). Las tres
# tablas por informe se retiraron con sus flujos, y `OPTIMIZE TABLE ... FINAL`
# sobre una tabla inexistente falla el DAG entero.
#
# En el modelo esta operación importa **más** que antes: sus hechos son
# `ReplacingMergeTree(version)`, y la fusión de versiones es justo lo que
# `OPTIMIZE FINAL` fuerza. Sin ella, `FINAL` en cada consulta paga el coste.
TABLAS_GESTIONADAS = [
    "dim_tiempo",
    "dim_geografia",
    "dim_severidad",
    "dim_origen_despacho",
    "dim_unidad",
    "hecho_accidente",
    "hecho_despacho",
    "hecho_estado_unidad",
    "hecho_ping_unidad",
    "etl_demo_principal",
    "dim_condado_vecino",
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
