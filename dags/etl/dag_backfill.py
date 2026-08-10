"""DAG de reproceso manual (backfill) para los DAGs de negocio `tactico`.

Reutiliza las MISMAS funciones `extract`/`transform`/`load` ya definidas en
cada DAG de negocio (`perdida_senal_dag.py`, `indice_calidad_dag.py`,
`rendimiento_proveedor_dag.py`) -- no hay una segunda implementación en
paralelo, para no arriesgar divergencia entre la corrida programada y un
backfill manual (prioridad de Mantenibilidad de la constitución del
proyecto).

Disparo manual únicamente (`schedule=None`), parametrizado con:
- `target`: dag_id del reporte a reprocesar.
- `start_date` / `end_date`: rango de fechas (inclusive) a reprocesar, un
  `ts` sintético por día a medianoche UTC (igual que el `schedule="@daily"`
  de los DAGs de negocio).

Usa Dynamic Task Mapping (`.expand`) para dar visibilidad por día en la UI
de Airflow en vez de un bucle opaco dentro de una sola tarea. Simplificación
conocida: `extract_backfill >> transform_backfill` no empareja por índice
-- Airflow espera a que TODAS las extracciones del rango terminen antes de
iniciar cualquier transformación. Es un backfill de reproceso histórico
(no tiempo real), así que esta espera por fases es aceptable.
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, "/opt/airflow/dags")

from airflow import DAG
from airflow.models.param import Param
from airflow.operators.python import PythonOperator

from lib.indice_calidad_tasks import extract as indice_calidad_extract
from lib.indice_calidad_tasks import load as indice_calidad_load
from lib.indice_calidad_tasks import transform as indice_calidad_transform
from lib.perdida_senal_tasks import extract as perdida_senal_extract
from lib.perdida_senal_tasks import load as perdida_senal_load
from lib.perdida_senal_tasks import transform as perdida_senal_transform
from lib.rendimiento_proveedor_tasks import extract as rendimiento_extract
from lib.rendimiento_proveedor_tasks import load as rendimiento_load
from lib.rendimiento_proveedor_tasks import transform as rendimiento_transform

DAG_ID = "backfill_manual"

TARGETS = {
    "perdida_senal_gps": (perdida_senal_extract, perdida_senal_transform, perdida_senal_load),
    "indice_calidad_historico": (indice_calidad_extract, indice_calidad_transform, indice_calidad_load),
    "rendimiento_por_proveedor": (rendimiento_extract, rendimiento_transform, rendimiento_load),
}


def build_date_range(**context) -> list[dict]:
    params = context["params"]
    inicio = datetime.strptime(params["start_date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
    fin = datetime.strptime(params["end_date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
    if fin < inicio:
        raise ValueError(f"end_date ({fin}) es anterior a start_date ({inicio})")

    target = params["target"]
    dias = []
    dia = inicio
    while dia <= fin:
        dias.append({"ts": dia.isoformat(), "target": target})
        dia += timedelta(days=1)
    return dias


def _dispatch(stage_index: int):
    def _run(ts: str, target: str, **_context) -> None:
        funcs = TARGETS[target]
        funcs[stage_index](ts=ts)

    return _run


with DAG(
    dag_id=DAG_ID,
    description="Reproceso manual de un rango de fechas para un DAG de negocio, vía las mismas funciones extract/transform/load ya programadas.",
    schedule=None,
    start_date=datetime(2026, 1, 1),
    catchup=False,
    is_paused_upon_creation=True,
    tags=["etl", "backfill"],
    params={
        "target": Param(
            "perdida_senal_gps",
            enum=list(TARGETS.keys()),
            description="DAG de negocio a reprocesar.",
        ),
        "start_date": Param("2026-01-01", format="date", description="Primer día a reprocesar (inclusive)."),
        "end_date": Param("2026-01-01", format="date", description="Último día a reprocesar (inclusive)."),
    },
) as dag:
    build_range_task = PythonOperator(task_id="build_date_range", python_callable=build_date_range)

    extract_backfill = PythonOperator.partial(
        task_id="extract_backfill", python_callable=_dispatch(0)
    ).expand(op_kwargs=build_range_task.output)

    transform_backfill = PythonOperator.partial(
        task_id="transform_backfill", python_callable=_dispatch(1)
    ).expand(op_kwargs=build_range_task.output)

    load_backfill = PythonOperator.partial(
        task_id="load_backfill", python_callable=_dispatch(2)
    ).expand(op_kwargs=build_range_task.output)

    build_range_task >> extract_backfill >> transform_backfill >> load_backfill
