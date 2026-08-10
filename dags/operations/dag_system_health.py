"""DAG: monitoreo sintético del stack `tactico` y su conectividad con Pinot.

Healthchecks HTTP simples (no un chequeo de negocio) sobre los mismos
endpoints que ya usan `lib/pinot_http_client.py` y
`lib/clickhouse_http_client.py`: confirma que el broker de Pinot responde
y que ClickHouse responde a `/ping`. Falla la tarea si alguno no responde,
dando visibilidad temprana en la UI de Airflow antes de que fallen los
DAGs de negocio por esa misma causa.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime

sys.path.insert(0, "/opt/airflow/dags")

import requests
from airflow import DAG
from airflow.exceptions import AirflowFailException
from airflow.operators.python import PythonOperator

DAG_ID = "system_health"

PINOT_BROKER_URL = os.environ.get("PINOT_BROKER_URL", "http://pinot-broker:8099")
CLICKHOUSE_URL = os.environ.get("CLICKHOUSE_URL", "http://tactico-clickhouse:8123")


def verificar_salud(**context) -> None:
    fallos = []

    try:
        resp = requests.get(f"{PINOT_BROKER_URL}/health", timeout=10)
        if resp.status_code != 200:
            fallos.append(f"Pinot broker respondió {resp.status_code}")
    except requests.RequestException as exc:
        fallos.append(f"Pinot broker inalcanzable: {exc}")

    try:
        resp = requests.get(f"{CLICKHOUSE_URL}/ping", timeout=10)
        if resp.status_code != 200:
            fallos.append(f"ClickHouse respondió {resp.status_code}")
    except requests.RequestException as exc:
        fallos.append(f"ClickHouse inalcanzable: {exc}")

    if fallos:
        raise AirflowFailException("Healthcheck falló:\n" + "\n".join(fallos))


with DAG(
    dag_id=DAG_ID,
    description="Healthcheck sintético de Pinot broker y ClickHouse.",
    schedule="*/15 * * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    is_paused_upon_creation=True,
    tags=["operations", "tactico"],
) as dag:
    verificar_salud_task = PythonOperator(task_id="verificar_salud", python_callable=verificar_salud)
