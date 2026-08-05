"""DAG: índice consolidado de calidad del histórico (informes tácticos compuestos, US2).

Reprocesa el histórico completo cada corrida (misma decisión que
`perdida_senal_dag.py`) y reemplaza `indice_calidad_historico` por período.
IDs de estado (DESCARTADO=7, FUSIONADO=8, CERRADO=6) replicados de
`backend/core/repositories/accidentes/estado_accidente_repository.ESTADO_IDS`
— el DAG no puede importar de `backend/` (ver research.md §2).
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone

sys.path.insert(0, "/opt/airflow/dags")

from airflow import DAG
from airflow.operators.python import PythonOperator

from lib.clickhouse_http_client import execute_clickhouse, insert_rows
from lib.ddl import ensure_indice_calidad_table
from lib.indice_calidad_logic import combinar_indice
from lib.pinot_http_client import query_pinot

DESCARTADO_ID = 7
FUSIONADO_ID = 8
CERRADO_ID = 6


def _periodo_str(epoch_ms: int) -> str:
    """DATETRUNC de Pinot devuelve epoch millis (LONG), no un string de fecha."""
    return datetime.fromtimestamp(epoch_ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d")


def _completitud_por_dia() -> dict[str, dict[str, float]]:
    rows = query_pinot(
        """
        SELECT DATETRUNC('day', fechahoraaccidente, 'MILLISECONDS') AS periodo,
               COUNT(*) AS total,
               SUM(CASE WHEN idseveridad IS NOT NULL AND idcalle IS NOT NULL THEN 1 ELSE 0 END) AS completos
        FROM Fact_Accidente
        GROUP BY periodo
        """
    )
    return {
        _periodo_str(r["periodo"]): {"total": r["total"], "completos": r["completos"] or 0} for r in rows
    }


def _descarte_fusion_por_dia() -> dict[str, dict[str, int]]:
    rows = query_pinot(
        f"""
        SELECT DATETRUNC('day', fechahoramodificado, 'MILLISECONDS') AS periodo,
               idtipoestadoincidente,
               COUNT(*) AS total
        FROM Fact_AccidenteTipoEstadoAccidente
        WHERE idtipoestadoincidente IN ({DESCARTADO_ID}, {FUSIONADO_ID})
        GROUP BY periodo, idtipoestadoincidente
        """
    )
    resultado: dict[str, dict[str, int]] = {}
    for r in rows:
        bucket = resultado.setdefault(_periodo_str(r["periodo"]), {"descartes": 0, "fusiones": 0})
        if r["idtipoestadoincidente"] == DESCARTADO_ID:
            bucket["descartes"] = r["total"]
        elif r["idtipoestadoincidente"] == FUSIONADO_ID:
            bucket["fusiones"] = r["total"]
    return resultado


def _cobertura_evidencia_por_dia() -> dict[str, dict[str, int]]:
    cerrados = query_pinot(
        f"""
        SELECT DATETRUNC('day', fechahoramodificado, 'MILLISECONDS') AS periodo, idaccidente
        FROM Fact_AccidenteTipoEstadoAccidente
        WHERE idtipoestadoincidente = {CERRADO_ID}
        """
    )
    con_evidencia = {r["idaccidente"] for r in query_pinot("SELECT DISTINCT idaccidente FROM Dim_EvidenciaFoto")}

    resultado: dict[str, dict[str, int]] = {}
    for r in cerrados:
        bucket = resultado.setdefault(_periodo_str(r["periodo"]), {"total_cerrados": 0, "con_evidencia": 0})
        bucket["total_cerrados"] += 1
        if r["idaccidente"] in con_evidencia:
            bucket["con_evidencia"] += 1
    return resultado


def run() -> None:
    ensure_indice_calidad_table()

    completitud = _completitud_por_dia()
    descarte_fusion = _descarte_fusion_por_dia()
    cobertura = _cobertura_evidencia_por_dia()

    calculado_en = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    filas = []
    for periodo, c in completitud.items():
        total = c["total"] or 1
        pct_completitud = c["completos"] / total

        df = descarte_fusion.get(periodo, {"descartes": 0, "fusiones": 0})
        pct_descarte = df["descartes"] / total
        pct_fusion = df["fusiones"] / total

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

    if not filas:
        return

    periodos = {f["periodo"] for f in filas}
    periodos_sql = ", ".join(f"'{p}'" for p in periodos)
    execute_clickhouse(f"ALTER TABLE indice_calidad_historico DELETE WHERE periodo IN ({periodos_sql})")
    insert_rows("indice_calidad_historico", filas)


with DAG(
    dag_id="indice_calidad_historico",
    description="Combina completitud/descarte/fusion/cobertura de evidencia en un índice único por período.",
    schedule="@daily",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    is_paused_upon_creation=True,
    tags=["informes-tacticos-compuestos"],
) as dag:
    run_task = PythonOperator(task_id="combinar_y_materializar", python_callable=run)
