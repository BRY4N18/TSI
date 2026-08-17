"""DAG: `hecho_validacion_region` del modelo analitico tactico (US2).

Septimo hecho. Sostiene los dos indicadores BSC de Red Operativa: la tasa de
aprobacion al primer intento y los motivos de rechazo.
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta

sys.path.insert(0, "/opt/airflow/dags")

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.sensors.external_task import ExternalTaskSensor

from lib.hecho_validacion_region_tasks import extract, load, transform

DAG_ID = "modelo_hecho_validacion_region"

with DAG(
    dag_id=DAG_ID,
    description=(
        "Carga hecho_validacion_region (hecho de transaccion, grano un intento "
        "de validacion, con numero_intento derivado y sin idusuario)."
    ),
    schedule="0 4 * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    is_paused_upon_creation=True,
    tags=["modelo-analitico", "hechos", "etl"],
) as dag:
    # La espera no es formal: sin las versiones de region cargadas, todas las
    # validaciones caerian en la region desconocida.
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
