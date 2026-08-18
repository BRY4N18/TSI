"""DAG: ciclo del prospecto — transicion de embudo y asignacion juntas.

Los dos hechos de Ventas y CRM que sostienen OT02. Se cargan en el mismo flujo
porque comparten fuente y porque un prospecto que cambia de etapa y de ejecutivo
el mismo dia es un solo ciclo.
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta

sys.path.insert(0, "/opt/airflow/dags")

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.sensors.external_task import ExternalTaskSensor

from lib.hecho_ciclo_prospecto_tasks import extract, load, transform

DAG_ID = "modelo_hecho_ciclo_prospecto"

with DAG(
    dag_id=DAG_ID,
    description=(
        "Carga hecho_transicion_embudo y hecho_asignacion_prospecto "
        "(ciclo del prospecto, grano una transicion / una asignacion)."
    ),
    schedule="0 4 * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    is_paused_upon_creation=True,
    tags=["modelo-analitico", "hechos", "etl", "ventas-crm"],
) as dag:
    esperar_dimensiones = ExternalTaskSensor(
        task_id="esperar_dimensiones",
        external_dag_id="modelo_dimensiones",
        external_task_id="load",
        # `modelo_dimensiones` corre a las 02:00 y este a las 04:00.
        execution_delta=timedelta(hours=2),
        mode="reschedule",
        timeout=60 * 60,
    )
    extract_task = PythonOperator(task_id="extract", python_callable=extract)
    transform_task = PythonOperator(task_id="transform", python_callable=transform)
    load_task = PythonOperator(task_id="load", python_callable=load)

    esperar_dimensiones >> extract_task >> transform_task >> load_task
