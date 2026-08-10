"""DAG: índice consolidado de calidad del histórico (informes tácticos compuestos, US2).

Reprocesa el histórico completo cada corrida (misma decisión que
`perdida_senal_dag.py`) y reemplaza `indice_calidad_historico` por período.

Patrón de staging en Parquet (ver `dags/lib/parquet_io.py`): las tareas en sí
viven en `dags/lib/indice_calidad_tasks.py` (no en este archivo) para que
`dag_backfill.py` pueda reutilizarlas sin importar un archivo de DAG desde
otro archivo de DAG (ver docstring de `dags/lib/perdida_senal_tasks.py`).
"""

from __future__ import annotations

import sys
from datetime import datetime

sys.path.insert(0, "/opt/airflow/dags")

from airflow import DAG
from airflow.operators.python import PythonOperator

from lib.indice_calidad_tasks import extract, load, transform

DAG_ID = "indice_calidad_historico"

with DAG(
    dag_id=DAG_ID,
    description="Combina completitud/descarte/fusion/cobertura de evidencia en un índice único por período (extract/transform/load-parquet).",
    schedule="@daily",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    is_paused_upon_creation=True,
    tags=["informes-tacticos-compuestos", "etl"],
) as dag:
    extract_task = PythonOperator(task_id="extract", python_callable=extract)
    transform_task = PythonOperator(task_id="transform", python_callable=transform)
    load_task = PythonOperator(task_id="load", python_callable=load)
    extract_task >> transform_task >> load_task
