"""DAG: `hecho_evidencia` del modelo analítico táctico (US3).

Quinto hecho del modelo. Sostiene los cinco informes de OT24 —cobertura,
latencia de sincronización, completitud de enriquecimiento, volumen por unidad y
escaladas de severidad—, ninguno de los cuales es calculable con las métricas del
caso: la evidencia tiene dos instantes propios y su grano no es el caso.
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta

sys.path.insert(0, "/opt/airflow/dags")

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.sensors.external_task import ExternalTaskSensor

from lib.hecho_evidencia_tasks import extract, load, transform

DAG_ID = "modelo_hecho_evidencia"

with DAG(
    dag_id=DAG_ID,
    description=(
        "Carga hecho_evidencia (hecho de transaccion, grano una evidencia "
        "capturada, sin idusuario ni enlace al material)."
    ),
    schedule="30 3 * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    is_paused_upon_creation=True,
    tags=["modelo-analitico", "hechos", "etl"],
) as dag:
    esperar_dimensiones = ExternalTaskSensor(
        task_id="esperar_dimensiones",
        external_dag_id="modelo_dimensiones",
        external_task_id="load",
        execution_delta=timedelta(hours=1, minutes=30),
        mode="reschedule",
        timeout=60 * 60,
    )
    # ⚠️ El segundo sensor no es redundante. Este hecho copia severidad y condado
    # **desde `hecho_accidente`**, no desde el origen. Sin esperarlo, correría
    # contra un hecho vacío o de ayer y las evidencias saldrían sin severidad:
    # el informe de cobertura por severidad quedaría vacío y nada fallaría.
    esperar_accidentes = ExternalTaskSensor(
        task_id="esperar_hecho_accidente",
        external_dag_id="modelo_hecho_accidente",
        external_task_id="load",
        # `modelo_hecho_accidente` corre a las 02:30 y este a las 03:30.
        execution_delta=timedelta(hours=1),
        mode="reschedule",
        timeout=60 * 60,
    )
    extract_task = PythonOperator(task_id="extract", python_callable=extract)
    transform_task = PythonOperator(task_id="transform", python_callable=transform)
    load_task = PythonOperator(task_id="load", python_callable=load)

    [esperar_dimensiones, esperar_accidentes] >> extract_task
    extract_task >> transform_task >> load_task
