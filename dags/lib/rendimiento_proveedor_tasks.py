"""Tareas extract/transform/load de `rendimiento_por_proveedor` (US3).

Separadas del archivo del DAG (`dags/etl/rendimiento_proveedor_dag.py`) para
que `dag_backfill.py` pueda reutilizarlas sin importar un archivo que a su
vez define un objeto `DAG` (ver docstring de
`dags/lib/perdida_senal_tasks.py` para la explicación completa del porqué).

Ver limitación de "proveedor vigente en el momento del despacho" en
`lib/rendimiento_proveedor_logic.py`.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

import pandas as pd

from lib.clickhouse_http_client import execute_clickhouse, insert_rows
from lib.ddl import ensure_rendimiento_proveedor_table
from lib.parquet_io import read_parquet, stage_path, write_parquet
from lib.pinot_http_client import query_pinot
from lib.rendimiento_proveedor_logic import agregar_por_proveedor


def _periodo_str(epoch_ms: int) -> str:
    return datetime.fromtimestamp(epoch_ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d")


def extract(**context) -> None:
    ts = context["ts"]

    despachos_raw = query_pinot(
        "SELECT iddespacho, idunidademergencia, fechahoradespacho, fechahorallegada FROM Fact_Despacho"
    )
    historial_raw = query_pinot("SELECT iddespacho, estadonuevo FROM Fact_HistorialDespachoUnidad")
    unidades_raw = query_pinot("SELECT idunidademergencia, idcliente FROM Dim_UnidadEmergencia")

    registros = [
        {"fuente": fuente, "payload": json.dumps(r)}
        for fuente, rows in (
            ("despachos", despachos_raw),
            ("historial", historial_raw),
            ("unidades", unidades_raw),
        )
        for r in rows
    ]
    write_parquet(pd.DataFrame(registros, columns=["fuente", "payload"]), stage_path(ts, "extract"))


def transform(**context) -> None:
    ts = context["ts"]
    df = read_parquet(stage_path(ts, "extract"))

    def _rows_for(fuente: str) -> list[dict]:
        if df.empty:
            return []
        return [json.loads(p) for p in df.loc[df["fuente"] == fuente, "payload"]]

    despachos = [
        {**d, "periodo": _periodo_str(d["fechahoradespacho"])}
        for d in _rows_for("despachos")
        if d.get("fechahoradespacho") is not None
    ]
    historial = _rows_for("historial")
    unidades = _rows_for("unidades")

    filas = agregar_por_proveedor(despachos, historial, unidades)

    calculado_en = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    for f in filas:
        f["calculado_en"] = calculado_en

    write_parquet(pd.DataFrame(filas), stage_path(ts, "transform"))


def load(**context) -> None:
    ts = context["ts"]
    df = read_parquet(stage_path(ts, "transform"))
    if df.empty:
        return

    ensure_rendimiento_proveedor_table()
    rows = df.to_dict("records")
    periodos = {r["periodo"] for r in rows}
    periodos_sql = ", ".join(f"'{p}'" for p in periodos)
    execute_clickhouse(f"ALTER TABLE rendimiento_por_proveedor DELETE WHERE periodo IN ({periodos_sql})")
    insert_rows("rendimiento_por_proveedor", rows)

    write_parquet(df, stage_path(ts, "load"))
