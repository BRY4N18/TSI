"""Staging en Parquet para el pipeline ETL de `tactico` (Pinot -> ClickHouse).

Cada tarea de un DAG (extract/transform/load) recalcula su propia ruta a
partir del `ts` de ejecución de Airflow -- no se usa XCom para pasar datos,
solo el archivo en disco. Esto hace que cada tarea sea re-ejecutable de forma
independiente desde la UI de Airflow (limpiar `transform` vuelve a leer el
mismo parquet de `extract`, de forma determinista).

Convención de ruta (decisión explícita del responsable del proyecto, sin
segmento de `dag_id`): `ETL/<fecha>/<hora>/<stage>_data.parquet`. Riesgo
aceptado: dos DAGs que corran en el mismo `ts` (p.ej. varios `@daily` a
medianoche) escriben en la misma carpeta y se pisan entre si -- no es un
bug, es una simplificación deliberada del layout.

Nota: el segmento `<hora>` usa `HH-MM` (guion), no `HH:MM` -- los dos
puntos no son válidos en rutas de Windows (verificado: Docker Desktop
remapea `:` silenciosamente al escribir al host vía bind mount, lo cual
no es un comportamiento confiable para dejarlo como está).
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

import pandas as pd

ETL_ROOT = Path(os.environ.get("ETL_ROOT", "/opt/airflow/ETL"))

STAGE_FILENAMES = {
    "extract": "extract_data.parquet",
    "transform": "transform_data.parquet",
    "load": "loading_data.parquet",
}


def stage_path(ts: str, stage: str, etl_root: Path | None = None) -> Path:
    """Construye ETL/<fecha>/<hora>/<stage>_data.parquet a partir de un ts ISO8601 de Airflow."""
    if stage not in STAGE_FILENAMES:
        raise ValueError(f"stage desconocido: {stage!r} (esperado uno de {sorted(STAGE_FILENAMES)})")
    dt = datetime.fromisoformat(ts)
    date_part = dt.strftime("%Y-%m-%d")
    time_part = dt.strftime("%H-%M")
    root = etl_root or ETL_ROOT
    return root / date_part / time_part / STAGE_FILENAMES[stage]


def write_parquet(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)


def read_parquet(path: Path) -> pd.DataFrame:
    return pd.read_parquet(path)
