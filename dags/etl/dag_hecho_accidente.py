"""DAG: `hecho_accidente` del modelo analítico táctico (T024).

**Espera al flujo de dimensiones**, no confía en el horario. Dos flujos `@daily`
no garantizan orden entre sí, y un hecho cargado antes que sus dimensiones se
queda con severidad, ciudad y condado en blanco — sin error y sin aviso.

El sensor se declara con `execution_delta` porque los dos flujos corren el mismo
día a horas distintas (dimensiones a las 02:00, este a las 02:30): sin ese
desfase, el sensor buscaría una corrida de dimensiones a las 02:30 que no existe
y esperaría para siempre.
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta

sys.path.insert(0, "/opt/airflow/dags")

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.sensors.external_task import ExternalTaskSensor

from lib.hecho_accidente_tasks import extract, load, transform

DAG_ID = "modelo_hecho_accidente"

with DAG(
    dag_id=DAG_ID,
    description=(
        "Carga hecho_accidente (instantánea acumulada, grano caso) con carga "
        "idempotente por partición mensual."
    ),
    schedule="30 2 * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    is_paused_upon_creation=True,
    tags=["modelo-analitico", "hechos", "etl"],
) as dag:
    esperar_dimensiones = ExternalTaskSensor(
        task_id="esperar_dimensiones",
        external_dag_id="modelo_dimensiones",
        external_task_id="load",
        execution_delta=timedelta(minutes=30),
        # Falla en vez de esperar indefinidamente: si las dimensiones no
        # corrieron, cargar el hecho igualmente sería peor que no cargarlo.
        mode="reschedule",
        timeout=60 * 60,
    )
    extract_task = PythonOperator(task_id="extract", python_callable=extract)
    transform_task = PythonOperator(task_id="transform", python_callable=transform)
    load_task = PythonOperator(task_id="load", python_callable=load)
    esperar_dimensiones >> extract_task >> transform_task >> load_task
