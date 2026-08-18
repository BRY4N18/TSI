"""DAG: nutricion del prospecto — demo y notificacion juntas.

Los dos hechos de Ventas y CRM que sostienen OT03. Se cargan en el mismo flujo
porque la latencia de reaccion se deriva cruzando el aviso con el primer avance
de etapa posterior.
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta

sys.path.insert(0, "/opt/airflow/dags")

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.sensors.external_task import ExternalTaskSensor

from lib.hecho_nutricion_tasks import extract, load, transform

DAG_ID = "modelo_hecho_nutricion"

with DAG(
    dag_id=DAG_ID,
    description=(
        "Carga hecho_interaccion_demo y hecho_notificacion_ventas "
        "(nutricion del prospecto; fuentes vacias hoy por entorno)."
    ),
    schedule="15 4 * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    is_paused_upon_creation=True,
    tags=["modelo-analitico", "hechos", "etl", "ventas-crm"],
) as dag:
    esperar_dimensiones = ExternalTaskSensor(
        task_id="esperar_dimensiones",
        external_dag_id="modelo_dimensiones",
        external_task_id="load",
        execution_delta=timedelta(hours=2, minutes=15),
        mode="reschedule",
        timeout=60 * 60,
    )
    extract_task = PythonOperator(task_id="extract", python_callable=extract)
    transform_task = PythonOperator(task_id="transform", python_callable=transform)
    load_task = PythonOperator(task_id="load", python_callable=load)

    esperar_dimensiones >> extract_task >> transform_task >> load_task
