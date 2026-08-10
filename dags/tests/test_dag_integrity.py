"""Smoke test estándar de Airflow: los DAGs cargan sin errores de import.

Archivo pytest plano, NO un DAG programado (confirmado explícitamente con
el responsable del proyecto). Sigue la misma convención de sys.path que el
resto de `dags/tests/` -- no hay `conftest.py` en este repo.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from airflow.models import DagBag  # noqa: E402

DAGS_FOLDER = str(Path(__file__).resolve().parents[1])

EXPECTED_DAG_IDS = {
    "perdida_senal_gps",
    "indice_calidad_historico",
    "rendimiento_por_proveedor",
    "etl_principal",
    "backfill_manual",
    "validacion_calidad_pipeline",
    "limpieza_staging",
    "mantenimiento_bd",
    "system_health",
}


def test_no_import_errors():
    dag_bag = DagBag(dag_folder=DAGS_FOLDER, include_examples=False)
    assert not dag_bag.import_errors, dag_bag.import_errors


def test_expected_dag_ids_present():
    dag_bag = DagBag(dag_folder=DAGS_FOLDER, include_examples=False)
    assert EXPECTED_DAG_IDS.issubset(set(dag_bag.dags.keys()))
