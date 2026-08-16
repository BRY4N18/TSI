"""DAG: `hecho_despacho` del modelo analítico táctico (T024).

Su dependencia de las dimensiones es **más fuerte** que la de `hecho_accidente`:
aquella copiaba etiquetas, esta resuelve la **atribución histórica** contra
`dim_unidad`. Sin sus versiones cargadas, todos los despachos caerían en la
versión desconocida y el hecho quedaría sin proveedor — que es precisamente la
cifra que este modelo existe para producir bien.
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta

sys.path.insert(0, "/opt/airflow/dags")

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.sensors.external_task import ExternalTaskSensor

from lib.hecho_despacho_tasks import extract, load, transform

DAG_ID = "modelo_hecho_despacho"

with DAG(
    dag_id=DAG_ID,
    description=(
        "Carga hecho_despacho (instantánea acumulada, grano intento) con atribución "
        "histórica de unidad a proveedor y carga idempotente por partición mensual."
    ),
    schedule="45 2 * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    is_paused_upon_creation=True,
    tags=["modelo-analitico", "hechos", "etl"],
) as dag:
    esperar_dimensiones = ExternalTaskSensor(
        task_id="esperar_dimensiones",
        external_dag_id="modelo_dimensiones",
        external_task_id="load",
        execution_delta=timedelta(minutes=45),
        mode="reschedule",
        timeout=60 * 60,
    )
    extract_task = PythonOperator(task_id="extract", python_callable=extract)
    transform_task = PythonOperator(task_id="transform", python_callable=transform)
    load_task = PythonOperator(task_id="load", python_callable=load)
    esperar_dimensiones >> extract_task >> transform_task >> load_task
