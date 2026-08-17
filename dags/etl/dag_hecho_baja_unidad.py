"""DAG: `hecho_baja_unidad` del modelo analítico táctico (Red Operativa, US1).

Sexto hecho del modelo. Sostiene los informes de **rotación de flota** y **bajas
forzadas**, ninguno calculable con métricas de la dimensión: la baja tiene
instante propio, y es el instante lo que miden los dos.
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta

sys.path.insert(0, "/opt/airflow/dags")

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.sensors.external_task import ExternalTaskSensor

from lib.hecho_baja_unidad_tasks import extract, load, transform

DAG_ID = "modelo_hecho_baja_unidad"

with DAG(
    dag_id=DAG_ID,
    description=(
        "Carga hecho_baja_unidad (hecho de transaccion, grano una baja de unidad, "
        "con proveedor por atribucion historica y sin idusuario)."
    ),
    schedule="45 3 * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    is_paused_upon_creation=True,
    tags=["modelo-analitico", "hechos", "etl"],
) as dag:
    # ⚠️ La espera no es formal. La baja resuelve su proveedor contra las
    # versiones de `dim_unidad`; sin ellas cargadas, todas las bajas caerían en
    # la unidad desconocida y el informe por proveedor saldría entero bajo
    # «Desconocido» sin que nada fallara.
    esperar_dimensiones = ExternalTaskSensor(
        task_id="esperar_dimensiones",
        external_dag_id="modelo_dimensiones",
        external_task_id="load",
        # `modelo_dimensiones` corre a las 02:00 y este a las 03:45.
        execution_delta=timedelta(hours=1, minutes=45),
        mode="reschedule",
        timeout=60 * 60,
    )
    extract_task = PythonOperator(task_id="extract", python_callable=extract)
    transform_task = PythonOperator(task_id="transform", python_callable=transform)
    load_task = PythonOperator(task_id="load", python_callable=load)

    esperar_dimensiones >> extract_task >> transform_task >> load_task
