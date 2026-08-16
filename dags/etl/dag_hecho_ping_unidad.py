"""DAG: `hecho_ping_unidad` del modelo analítico táctico (fase 6).

Sostiene el informe de pérdida de señal desde el modelo, que es la condición
para retirar su tabla propia.
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta

sys.path.insert(0, "/opt/airflow/dags")

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.sensors.external_task import ExternalTaskSensor

from lib.hecho_ping_unidad_tasks import extract, load, transform

DAG_ID = "modelo_hecho_ping_unidad"

with DAG(
    dag_id=DAG_ID,
    description=(
        "Carga hecho_ping_unidad (hecho de transacción, grano posición reportada, "
        "sin coordenadas) para el análisis de continuidad de señal."
    ),
    schedule="15 3 * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    is_paused_upon_creation=True,
    tags=["modelo-analitico", "hechos", "etl"],
) as dag:
    esperar_dimensiones = ExternalTaskSensor(
        task_id="esperar_dimensiones",
        external_dag_id="modelo_dimensiones",
        external_task_id="load",
        execution_delta=timedelta(hours=1, minutes=15),
        mode="reschedule",
        timeout=60 * 60,
    )
    extract_task = PythonOperator(task_id="extract", python_callable=extract)
    transform_task = PythonOperator(task_id="transform", python_callable=transform)
    load_task = PythonOperator(task_id="load", python_callable=load)
    esperar_dimensiones >> extract_task >> transform_task >> load_task
