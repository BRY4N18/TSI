"""DAG: limpieza de staging Parquet vencido en `ETL/`.

Borra carpetas `ETL/<fecha>/<hora>/` cuya fecha sea más antigua que el
umbral de retención (Airflow Variable `etl_retention_days`, default 7 días).
Los parquet ya fueron cargados a ClickHouse por los DAGs de negocio -- son
staging, no el almacén de registro (ver `.specify/docs/infra/infrastructure.md`),
así que es seguro borrarlos pasado el umbral.
"""

from __future__ import annotations

import shutil
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, "/opt/airflow/dags")

from airflow import DAG
from airflow.models import Variable
from airflow.operators.python import PythonOperator

from lib.parquet_io import ETL_ROOT

DAG_ID = "limpieza_staging"

DEFAULT_RETENTION_DAYS = 7


def limpiar(**context) -> None:
    retention_days = int(Variable.get("etl_retention_days", default_var=DEFAULT_RETENTION_DAYS))
    limite = datetime.now(timezone.utc).date() - timedelta(days=retention_days)

    if not ETL_ROOT.exists():
        return

    borradas = []
    for carpeta_fecha in ETL_ROOT.iterdir():
        if not carpeta_fecha.is_dir():
            continue
        try:
            fecha = datetime.strptime(carpeta_fecha.name, "%Y-%m-%d").date()
        except ValueError:
            continue  # no es una carpeta de fecha (p.ej. .gitkeep) -- se ignora
        if fecha < limite:
            shutil.rmtree(carpeta_fecha)
            borradas.append(carpeta_fecha.name)

    context["ti"].log.info("Carpetas ETL borradas (retención=%s días): %s", retention_days, borradas)


with DAG(
    dag_id=DAG_ID,
    description="Borra staging Parquet en ETL/ más antiguo que el umbral de retención.",
    schedule="@weekly",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    is_paused_upon_creation=True,
    tags=["operations", "tactico"],
) as dag:
    limpiar_task = PythonOperator(task_id="limpiar", python_callable=limpiar)
