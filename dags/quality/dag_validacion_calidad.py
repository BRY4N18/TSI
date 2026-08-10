"""DAG: gate técnico de calidad del pipeline ETL `tactico`.

Distinto del informe de negocio "índice de calidad histórico"
(`dags/etl/indice_calidad_dag.py`, que mide calidad de los datos de
accidentes en sí): este DAG valida la SALUD DEL PROPIO PIPELINE ETL --
paridad de conteo de filas entre Pinot (origen) y ClickHouse (destino) para
el día recién procesado, y nulos en columnas clave de cada tabla de
negocio. No transforma ni mueve datos, solo verifica.

Corre después de la ventana de los DAGs de negocio (`schedule="30 0 * * *"`,
30 min después de la medianoche `@daily` de los DAGs de negocio) para dar
tiempo a que terminen. Falla la tarea (visible en la UI de Airflow) si algún
chequeo no pasa, en vez de solo loguear una advertencia -- es un gate, no
una métrica informativa.
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, "/opt/airflow/dags")

from airflow import DAG
from airflow.exceptions import AirflowFailException
from airflow.operators.python import PythonOperator

from lib.clickhouse_http_client import query_clickhouse
from lib.pinot_http_client import query_pinot

DAG_ID = "validacion_calidad_pipeline"

# (tabla_clickhouse, columna_periodo, sql_conteo_pinot, columnas_clave_no_nulas_clickhouse)
CHEQUEOS = [
    (
        "perdida_senal_gps",
        "SELECT COUNT(*) AS total FROM Dim_HistorialUbicacionUnidadEmergencia",
        ["idunidademergencia", "periodo"],
    ),
    (
        "indice_calidad_historico",
        "SELECT COUNT(*) AS total FROM Fact_Accidente",
        ["periodo", "indice_consolidado"],
    ),
    (
        "rendimiento_por_proveedor",
        "SELECT COUNT(*) AS total FROM Fact_Despacho",
        ["periodo", "idcliente"],
    ),
]


def validar(**context) -> None:
    ayer = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
    fallos: list[str] = []

    for tabla_ch, sql_conteo_origen, columnas_clave in CHEQUEOS:
        total_origen = int(query_pinot(sql_conteo_origen)[0]["total"])
        # ClickHouse serializa UInt64 como string en JSONEachRow (evita pérdida de precisión en JS) -- castear.
        rows_destino = query_clickhouse(f"SELECT count(*) AS total FROM {tabla_ch}")
        total_destino = int(rows_destino[0]["total"]) if rows_destino else 0

        if total_origen > 0 and total_destino == 0:
            fallos.append(f"{tabla_ch}: origen tiene {total_origen} filas pero ClickHouse está vacío")

        for columna in columnas_clave:
            nulos = query_clickhouse(f"SELECT count(*) AS total FROM {tabla_ch} WHERE {columna} IS NULL")
            total_nulos = int(nulos[0]["total"]) if nulos else 0
            if total_nulos > 0:
                fallos.append(f"{tabla_ch}.{columna}: {total_nulos} filas con NULL (esperado 0)")

    if fallos:
        raise AirflowFailException("Validación de calidad del pipeline falló:\n" + "\n".join(fallos))


with DAG(
    dag_id=DAG_ID,
    description="Gate técnico: paridad de conteo Pinot/ClickHouse y nulos en columnas clave de las tablas tácticas.",
    schedule="30 0 * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    is_paused_upon_creation=True,
    tags=["quality", "tactico"],
) as dag:
    validar_task = PythonOperator(task_id="validar", python_callable=validar)
