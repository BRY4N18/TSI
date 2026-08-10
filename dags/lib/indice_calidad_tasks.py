"""Tareas extract/transform/load de `indice_calidad_historico` (US2).

Separadas del archivo del DAG (`dags/etl/indice_calidad_dag.py`) para que
`dag_backfill.py` pueda reutilizarlas sin importar un archivo que a su vez
define un objeto `DAG` (ver docstring de `dags/lib/perdida_senal_tasks.py`
para la explicación completa del porqué).

IDs de estado (DESCARTADO=7, FUSIONADO=8, CERRADO=6) replicados de
`backend/core/repositories/accidentes/estado_accidente_repository.ESTADO_IDS`
— este módulo no puede importar de `backend/` (ver research.md §2).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

import pandas as pd

from lib.clickhouse_http_client import execute_clickhouse, insert_rows
from lib.ddl import ensure_indice_calidad_table
from lib.indice_calidad_logic import combinar_indice
from lib.parquet_io import read_parquet, stage_path, write_parquet
from lib.pinot_http_client import query_pinot

DESCARTADO_ID = 7
FUSIONADO_ID = 8
CERRADO_ID = 6


def _periodo_str(epoch_ms: int) -> str:
    """DATETRUNC de Pinot devuelve epoch millis (LONG), no un string de fecha."""
    return datetime.fromtimestamp(epoch_ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d")


def _completitud_por_dia(rows: list[dict]) -> dict[str, dict[str, float]]:
    return {
        _periodo_str(r["periodo"]): {"total": r["total"], "completos": r["completos"] or 0} for r in rows
    }


def _descarte_fusion_por_dia(rows: list[dict]) -> dict[str, dict[str, int]]:
    resultado: dict[str, dict[str, int]] = {}
    for r in rows:
        bucket = resultado.setdefault(_periodo_str(r["periodo"]), {"descartes": 0, "fusiones": 0})
        if r["idtipoestadoincidente"] == DESCARTADO_ID:
            bucket["descartes"] = r["total"]
        elif r["idtipoestadoincidente"] == FUSIONADO_ID:
            bucket["fusiones"] = r["total"]
    return resultado


def _cobertura_evidencia_por_dia(cerrados: list[dict], evidencia: list[dict]) -> dict[str, dict[str, int]]:
    con_evidencia = {r["idaccidente"] for r in evidencia}
    resultado: dict[str, dict[str, int]] = {}
    for r in cerrados:
        bucket = resultado.setdefault(_periodo_str(r["periodo"]), {"total_cerrados": 0, "con_evidencia": 0})
        bucket["total_cerrados"] += 1
        if r["idaccidente"] in con_evidencia:
            bucket["con_evidencia"] += 1
    return resultado


def extract(**context) -> None:
    ts = context["ts"]

    completitud_raw = query_pinot(
        """
        SELECT DATETRUNC('day', fechahoraaccidente, 'MILLISECONDS') AS periodo,
               COUNT(*) AS total,
               SUM(CASE WHEN idseveridad IS NOT NULL AND idcalle IS NOT NULL THEN 1 ELSE 0 END) AS completos
        FROM Fact_Accidente
        GROUP BY periodo
        """
    )
    descarte_fusion_raw = query_pinot(
        f"""
        SELECT DATETRUNC('day', fechahoramodificado, 'MILLISECONDS') AS periodo,
               idtipoestadoincidente,
               COUNT(*) AS total
        FROM Fact_AccidenteTipoEstadoAccidente
        WHERE idtipoestadoincidente IN ({DESCARTADO_ID}, {FUSIONADO_ID})
        GROUP BY periodo, idtipoestadoincidente
        """
    )
    cobertura_cerrados_raw = query_pinot(
        f"""
        SELECT DATETRUNC('day', fechahoramodificado, 'MILLISECONDS') AS periodo, idaccidente
        FROM Fact_AccidenteTipoEstadoAccidente
        WHERE idtipoestadoincidente = {CERRADO_ID}
        """
    )
    evidencia_raw = query_pinot("SELECT DISTINCT idaccidente FROM Dim_EvidenciaFoto")

    registros = [
        {"fuente": fuente, "payload": json.dumps(r)}
        for fuente, rows in (
            ("completitud", completitud_raw),
            ("descarte_fusion", descarte_fusion_raw),
            ("cobertura_cerrados", cobertura_cerrados_raw),
            ("evidencia", evidencia_raw),
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

    completitud = _completitud_por_dia(_rows_for("completitud"))
    descarte_fusion = _descarte_fusion_por_dia(_rows_for("descarte_fusion"))
    cobertura = _cobertura_evidencia_por_dia(_rows_for("cobertura_cerrados"), _rows_for("evidencia"))

    calculado_en = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    filas = []
    for periodo, c in completitud.items():
        total = c["total"] or 1
        pct_completitud = c["completos"] / total

        dfusion = descarte_fusion.get(periodo, {"descartes": 0, "fusiones": 0})
        pct_descarte = dfusion["descartes"] / total
        pct_fusion = dfusion["fusiones"] / total

        cob = cobertura.get(periodo, {"total_cerrados": 0, "con_evidencia": 0})
        pct_cobertura = (cob["con_evidencia"] / cob["total_cerrados"]) if cob["total_cerrados"] else 1.0

        indice = combinar_indice(pct_completitud, pct_descarte, pct_fusion, pct_cobertura)
        filas.append(
            {
                "periodo": periodo,
                "pct_completitud": round(pct_completitud, 4),
                "pct_descarte": round(pct_descarte, 4),
                "pct_fusion": round(pct_fusion, 4),
                "pct_cobertura_evidencia": round(pct_cobertura, 4),
                "indice_consolidado": indice,
                "calculado_en": calculado_en,
            }
        )

    write_parquet(pd.DataFrame(filas), stage_path(ts, "transform"))


def load(**context) -> None:
    ts = context["ts"]
    df = read_parquet(stage_path(ts, "transform"))
    if df.empty:
        return

    ensure_indice_calidad_table()
    rows = df.to_dict("records")
    periodos = {r["periodo"] for r in rows}
    periodos_sql = ", ".join(f"'{p}'" for p in periodos)
    execute_clickhouse(f"ALTER TABLE indice_calidad_historico DELETE WHERE periodo IN ({periodos_sql})")
    insert_rows("indice_calidad_historico", rows)

    write_parquet(df, stage_path(ts, "load"))
