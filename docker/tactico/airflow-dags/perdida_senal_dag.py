"""DAG: detección de pérdida de señal GPS (informes tácticos compuestos, US1).

Decisión de idempotencia (FR-003, SC-003): cada corrida reprocesa el histórico
completo disponible en Pinot (no una ventana incremental) y reemplaza el
contenido de `perdida_senal_gps` por período recalculado (`ALTER ... DELETE`
del rango + `INSERT` fresco). Es razonable para el volumen de datos de este
proyecto (ver `.specify/docs/infra/infrastructure.md`, proyecto individual);
si el volumen de pings creciera mucho, la ventana debería acotarse a un
incremental — no es necesario en esta primera versión.
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from itertools import groupby

sys.path.insert(0, "/opt/airflow/dags")

from airflow import DAG
from airflow.operators.python import PythonOperator

from lib.clickhouse_http_client import execute_clickhouse, insert_rows
from lib.ddl import ensure_perdida_senal_table
from lib.perdida_senal_logic import detectar_huecos
from lib.pinot_http_client import query_pinot


def _umbral_vigente() -> int:
    rows = query_pinot(
        "SELECT gps_umbral_senal_perdida_seg FROM Dim_ParametrosSeguimiento ORDER BY idparametrosseguimiento DESC LIMIT 1"
    )
    # Fallback 60s = default real de SEGUIMIENTO_PARAMETROS en backend/config/settings.py
    # (Dim_ParametrosSeguimiento en Pinot solo registra overrides auditables, no el default).
    return int(rows[0]["gps_umbral_senal_perdida_seg"]) if rows else 60


def run() -> None:
    ensure_perdida_senal_table()
    umbral = _umbral_vigente()

    pings = query_pinot("SELECT idunidademergencia, idaccidente, fechahora FROM Dim_HistorialUbicacionUnidadEmergencia")
    pings.sort(key=lambda p: p["idunidademergencia"])

    huecos_totales = []
    for _, grupo in groupby(pings, key=lambda p: p["idunidademergencia"]):
        huecos_totales.extend(detectar_huecos(list(grupo), umbral))

    if not huecos_totales:
        return

    calculado_en = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    for h in huecos_totales:
        h["periodo"] = h["inicio_hueco"][:10]
        h["calculado_en"] = calculado_en

    periodos = {h["periodo"] for h in huecos_totales}
    periodos_sql = ", ".join(f"'{p}'" for p in periodos)
    execute_clickhouse(f"ALTER TABLE perdida_senal_gps DELETE WHERE periodo IN ({periodos_sql})")
    insert_rows("perdida_senal_gps", huecos_totales)


with DAG(
    dag_id="perdida_senal_gps",
    description="Detecta huecos de señal GPS por unidad, materializa en ClickHouse.",
    schedule="@daily",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    is_paused_upon_creation=True,
    tags=["informes-tacticos-compuestos"],
) as dag:
    run_task = PythonOperator(task_id="detectar_y_materializar", python_callable=run)
