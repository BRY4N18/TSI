"""DAG: rendimiento de despacho por proveedor de unidades (informes tácticos compuestos, US3).

Reprocesa el histórico completo cada corrida (misma decisión que los otros 2
DAGs) y reemplaza `rendimiento_por_proveedor` por período. Ver limitación de
"proveedor vigente en el momento del despacho" en `lib/rendimiento_proveedor_logic.py`.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone

sys.path.insert(0, "/opt/airflow/dags")

from airflow import DAG
from airflow.operators.python import PythonOperator

from lib.clickhouse_http_client import execute_clickhouse, insert_rows
from lib.ddl import ensure_rendimiento_proveedor_table
from lib.pinot_http_client import query_pinot
from lib.rendimiento_proveedor_logic import agregar_por_proveedor


def _periodo_str(epoch_ms: int) -> str:
    return datetime.fromtimestamp(epoch_ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d")


def run() -> None:
    ensure_rendimiento_proveedor_table()

    despachos_raw = query_pinot(
        "SELECT iddespacho, idunidademergencia, fechahoradespacho, fechahorallegada FROM Fact_Despacho"
    )
    despachos = [
        {**d, "periodo": _periodo_str(d["fechahoradespacho"])}
        for d in despachos_raw
        if d.get("fechahoradespacho") is not None
    ]

    historial = query_pinot("SELECT iddespacho, estadonuevo FROM Fact_HistorialDespachoUnidad")
    unidades = query_pinot("SELECT idunidademergencia, idcliente FROM Dim_UnidadEmergencia")

    filas = agregar_por_proveedor(despachos, historial, unidades)
    if not filas:
        return

    calculado_en = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    for f in filas:
        f["calculado_en"] = calculado_en

    periodos = {f["periodo"] for f in filas}
    periodos_sql = ", ".join(f"'{p}'" for p in periodos)
    execute_clickhouse(f"ALTER TABLE rendimiento_por_proveedor DELETE WHERE periodo IN ({periodos_sql})")
    insert_rows("rendimiento_por_proveedor", filas)


with DAG(
    dag_id="rendimiento_por_proveedor",
    description="Agrega rendimiento de despacho por proveedor de unidades (idcliente), materializa en ClickHouse.",
    schedule="@daily",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    is_paused_upon_creation=True,
    tags=["informes-tacticos-compuestos"],
) as dag:
    run_task = PythonOperator(task_id="agregar_y_materializar", python_callable=run)
