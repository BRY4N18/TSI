"""DAG: dimensiones del modelo analítico táctico (T019).

**Corre antes que cualquier flujo de hechos.** Los dos DAGs de hechos declaran
un sensor sobre este, en vez de confiar en que el horario los ordene: dos flujos
`@daily` no garantizan orden entre sí.

Horario adelantado media hora respecto a los hechos para que, en la corrida
normal, las dimensiones ya estén cuando los hechos las busquen.
"""

from __future__ import annotations

import sys
from datetime import datetime

sys.path.insert(0, "/opt/airflow/dags")

from airflow import DAG
from airflow.operators.python import PythonOperator

from lib.dimensiones_tasks import extract, load, transform

DAG_ID = "modelo_dimensiones"

with DAG(
    dag_id=DAG_ID,
    description=(
        "Carga las 5 dimensiones del modelo analítico (tiempo, geografía, severidad, "
        "origen de despacho y unidad versionada). Debe correr antes que los hechos."
    ),
    schedule="0 2 * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    is_paused_upon_creation=True,
    tags=["modelo-analitico", "dimensiones", "etl"],
) as dag:
    extract_task = PythonOperator(task_id="extract", python_callable=extract)
    transform_task = PythonOperator(task_id="transform", python_callable=transform)
    load_task = PythonOperator(task_id="load", python_callable=load)
    extract_task >> transform_task >> load_task
