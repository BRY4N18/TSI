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

# ⚠️ Los tres DAGs por informe —`perdida_senal_gps`, `indice_calidad_historico`
# y `rendimiento_por_proveedor`— y `backfill_manual` se retiraron el 2026-08-15
# (decisión #20, opción B). El modelo analítico calcula lo mismo, y mejor: las
# consultas viejas truncaban en silencio a 10 000 filas.
#
# `backfill_manual` existía solo para reprocesar esas tres tablas; en el modelo,
# reprocesar es volver a correr el DAG, porque `ReplacingMergeTree(version)`
# sustituye por versión.
EXPECTED_DAG_IDS = {
    "etl_principal",
    "validacion_calidad_pipeline",
    "limpieza_staging",
    "mantenimiento_bd",
    "system_health",
    "modelo_dimensiones",
    "modelo_hecho_accidente",
    "modelo_hecho_despacho",
    "modelo_hecho_estado_unidad",
    "modelo_hecho_ping_unidad",
    "modelo_hecho_evidencia",
    "modelo_hecho_baja_unidad",
    "modelo_hecho_validacion_region",
    "modelo_hecho_ciclo_prospecto",
    "modelo_hecho_nutricion",
    "modelo_hecho_suscripcion",
    "modelo_hecho_facturacion",
    "modelo_hecho_soporte",
    "modelo_hecho_sesion",
    "modelo_hecho_onboarding",
    "modelo_hecho_llamada_api",
    "modelo_hecho_cambio_acceso",
}


def test_no_import_errors():
    dag_bag = DagBag(dag_folder=DAGS_FOLDER, include_examples=False)
    assert not dag_bag.import_errors, dag_bag.import_errors


def test_expected_dag_ids_present():
    dag_bag = DagBag(dag_folder=DAGS_FOLDER, include_examples=False)
    assert EXPECTED_DAG_IDS.issubset(set(dag_bag.dags.keys()))
