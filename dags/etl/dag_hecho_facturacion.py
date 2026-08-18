"""DAG: facturación — factura y solicitud de cambio de plan juntas."""

from __future__ import annotations

import sys
from datetime import datetime, timedelta

sys.path.insert(0, "/opt/airflow/dags")

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.sensors.external_task import ExternalTaskSensor

from lib.hecho_facturacion_tasks import extract, load, transform

DAG_ID = "modelo_hecho_facturacion"

with DAG(
    dag_id=DAG_ID,
    description=(
        "Carga hecho_factura y hecho_solicitud_cambio_plan "
        "(transacción, grano una factura / una solicitud)."
    ),
    schedule="30 3 * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    is_paused_upon_creation=True,
    tags=["modelo-analitico", "hechos", "etl", "suscripciones"],
) as dag:
    esperar_dimensiones = ExternalTaskSensor(
        task_id="esperar_dimensiones",
        external_dag_id="modelo_dimensiones",
        external_task_id="load",
        execution_delta=timedelta(hours=1, minutes=30),
        mode="reschedule",
        timeout=60 * 60,
    )
    extract_task = PythonOperator(task_id="extract", python_callable=extract)
    transform_task = PythonOperator(task_id="transform", python_callable=transform)
    load_task = PythonOperator(task_id="load", python_callable=load)

    esperar_dimensiones >> extract_task >> transform_task >> load_task
