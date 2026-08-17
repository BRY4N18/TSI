"""Plomería compartida por los tres flujos del modelo: parquet ↔ filas.

Existe porque el paso por parquet **no es neutro con la ausencia**. Pandas no
tiene enteros ausentes en una columna de enteros: convierte la columna a decimal
y pone `NaN`. Si esas filas se insertaran tal cual, un hito no alcanzado llegaría
al almacén como `NaN` —o peor, como `0` tras una conversión— y se habría perdido
justo la distinción que el modelo entero defiende.

Aquí se restituye: **todo lo que pandas marcó ausente vuelve a ser ausente**, y
los tipos de numpy vuelven a ser tipos de Python, que es lo que el serializador
del almacén sabe escribir.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Mapping

import pandas as pd

from lib.parquet_io import read_parquet, stage_path, write_parquet


def ruta(ts: str, stage: str, prefijo: str) -> Path:
    return stage_path(ts, stage, prefijo=prefijo)


def guardar(filas: Iterable[Mapping[str, Any]], destino: Path) -> int:
    """Escribe las filas y devuelve cuántas. Un lote vacío también se escribe:
    su ausencia y un fichero vacío significan cosas distintas al depurar."""
    marco = pd.DataFrame(list(filas))
    write_parquet(marco, destino)
    return len(marco)


def _valor(valor: Any) -> Any:
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return None
    # ⚠️ Las columnas de array vuelven del parquet como `ndarray`, que **tambien**
    # tiene `.item()` — y ahi `.item()` no convierte el array, exige que tenga un
    # solo elemento y falla con «can only convert an array of size 1 to a Python
    # scalar». El mensaje no menciona ni la columna ni el tipo, y el fallo ocurre
    # dos pasos despues de donde esta la causa.
    #
    # La primera columna de array del modelo es `dim_geografia.condados_vecinos`;
    # hasta ella, ninguna lo era, y por eso este `hasattr` bastaba.
    if hasattr(valor, "tolist"):  # arrays de numpy
        return valor.tolist()
    if hasattr(valor, "item"):  # escalares de numpy
        return valor.item()
    return valor


def cargar(origen: Path) -> list[dict[str, Any]]:
    """Lee un parquet y devuelve filas **con la ausencia restituida**."""
    marco = read_parquet(origen)
    if marco.empty:
        return []
    return [
        {clave: _valor(valor) for clave, valor in fila.items()}
        for fila in marco.to_dict(orient="records")
    ]
