"""Ayuda compartida por las pruebas que van contra el almacén de verdad.

Las pruebas de las fases 1 y 2 son de lógica pura y corren en cualquier sitio.
Estas no: comprueban **el modelo cargado**, y por tanto necesitan el stack
táctico levantado. Se saltan solas si no lo encuentran, en vez de fallar — un
fallo rojo por «no hay stack» entrena a ignorar los fallos rojos.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.clickhouse_http_client import query_clickhouse  # noqa: E402

#: Partición muy posterior a cualquier dato real. Las pruebas que necesitan
#: escribir lo hacen aquí y la descartan al terminar, para no tocar nunca las
#: cifras que otra prueba está comprobando.
PARTICION_DE_PRUEBA = 209912
FECHA_DE_PRUEBA = "2099-12-01"


def almacen_disponible() -> bool:
    try:
        query_clickhouse("SELECT 1")
        return True
    except Exception:  # noqa: BLE001
        return False


def modelo_cargado() -> bool:
    """El almacén responde **y** los hechos tienen datos."""
    if not almacen_disponible():
        return False
    try:
        return int(query_clickhouse("SELECT count() AS n FROM hecho_accidente")[0]["n"]) > 0
    except Exception:  # noqa: BLE001
        return False


requiere_modelo = pytest.mark.skipif(
    not modelo_cargado(),
    reason="requiere el stack táctico levantado y el modelo cargado",
)


def contar(sql: str) -> int:
    return int(query_clickhouse(sql)[0]["n"])
