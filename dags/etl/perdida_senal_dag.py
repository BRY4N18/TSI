"""DAG: detección de pérdida de señal GPS (informes tácticos compuestos, US1).

Decisión de idempotencia (FR-003, SC-003): cada corrida reprocesa el histórico
completo disponible en Pinot (no una ventana incremental) y reemplaza el
contenido de `perdida_senal_gps` por período recalculado (`ALTER ... DELETE`
del rango + `INSERT` fresco). Es razonable para el volumen de datos de este
proyecto (ver `.specify/docs/infra/infrastructure.md`, proyecto individual);
si el volumen de pings creciera mucho, la ventana debería acotarse a un
incremental — no es necesario en esta primera versión.

Patrón de staging en Parquet (ver `dags/lib/parquet_io.py`): 3 tareas
independientes (extract/transform/load) que se pasan datos vía archivos
parquet en `ETL/<fecha>/<hora>/`, no vía XCom. Las funciones en sí viven en
`dags/lib/perdida_senal_tasks.py` (no en este archivo) para que
`dag_backfill.py` pueda reutilizarlas sin importar un archivo de DAG desde
otro archivo de DAG (ver docstring de ese módulo).
"""

from __future__ import annotations

import sys
from datetime import datetime

sys.path.insert(0, "/opt/airflow/dags")

from airflow import DAG
from airflow.operators.python import PythonOperator

from lib.perdida_senal_tasks import extract, load, transform

DAG_ID = "perdida_senal_gps"

with DAG(
    dag_id=DAG_ID,
    description="Detecta huecos de señal GPS por unidad, materializa en ClickHouse (extract/transform/load-parquet).",
    schedule="@daily",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    is_paused_upon_creation=True,
    tags=["informes-tacticos-compuestos", "etl"],
) as dag:
    extract_task = PythonOperator(task_id="extract", python_callable=extract)
    transform_task = PythonOperator(task_id="transform", python_callable=transform)
    load_task = PythonOperator(task_id="load", python_callable=load)
    extract_task >> transform_task >> load_task
