"""Tareas extract/transform/load de `perdida_senal_gps` (US1).

Separadas del archivo del DAG (`dags/etl/perdida_senal_dag.py`) para que
`dag_backfill.py` pueda reutilizarlas sin importar un archivo que a su vez
define un objeto `DAG` -- Airflow re-registra (y falla con
`AirflowDagDuplicatedIdException`) un DAG cuyo archivo es importado desde
otro archivo de DAG. Este módulo no define ningún `DAG`, solo funciones.
"""

from __future__ import annotations

from datetime import datetime, timezone
from itertools import groupby

import pandas as pd

from lib.clickhouse_http_client import execute_clickhouse, insert_rows
from lib.ddl import ensure_perdida_senal_table
from lib.parquet_io import read_parquet, stage_path, write_parquet
from lib.perdida_senal_logic import detectar_huecos
from lib.pinot_http_client import query_pinot


def _umbral_vigente() -> int:
    rows = query_pinot(
        "SELECT gps_umbral_senal_perdida_seg FROM Dim_ParametrosSeguimiento ORDER BY idparametrosseguimiento DESC LIMIT 1"
    )
    # Fallback 60s = default real de SEGUIMIENTO_PARAMETROS en backend/config/settings.py
    # (Dim_ParametrosSeguimiento en Pinot solo registra overrides auditables, no el default).
    return int(rows[0]["gps_umbral_senal_perdida_seg"]) if rows else 60


def extract(**context) -> None:
    ts = context["ts"]
    pings = query_pinot("SELECT idunidademergencia, idaccidente, fechahora FROM Dim_HistorialUbicacionUnidadEmergencia")
    write_parquet(pd.DataFrame(pings), stage_path(ts, "extract"))


def transform(**context) -> None:
    ts = context["ts"]
    df = read_parquet(stage_path(ts, "extract"))
    umbral = _umbral_vigente()

    huecos_totales: list[dict] = []
    if not df.empty:
        pings = df.sort_values("idunidademergencia").to_dict("records")
        for _, grupo in groupby(pings, key=lambda p: p["idunidademergencia"]):
            huecos_totales.extend(detectar_huecos(list(grupo), umbral))

    calculado_en = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    for h in huecos_totales:
        h["periodo"] = h["inicio_hueco"][:10]
        h["calculado_en"] = calculado_en

    write_parquet(pd.DataFrame(huecos_totales), stage_path(ts, "transform"))


def load(**context) -> None:
    ts = context["ts"]
    df = read_parquet(stage_path(ts, "transform"))
    if df.empty:
        return

    ensure_perdida_senal_table()
    rows = df.to_dict("records")
    periodos = {r["periodo"] for r in rows}
    periodos_sql = ", ".join(f"'{p}'" for p in periodos)
    execute_clickhouse(f"ALTER TABLE perdida_senal_gps DELETE WHERE periodo IN ({periodos_sql})")
    insert_rows("perdida_senal_gps", rows)

    write_parquet(df, stage_path(ts, "load"))
