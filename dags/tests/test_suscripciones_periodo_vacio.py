"""T066 — un período sin datos devuelve cero filas, no una fila de ceros."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.consultas import listar  # noqa: E402

from tests.almacen import (  # noqa: E402
    asegurar_hechos_suscripciones,
    ejecutar_suscripciones,
    requiere_modelo,
)

INFORMES = listar("suscripciones")
VACIO = "1999-01-01"


@requiere_modelo
@pytest.mark.parametrize("informe", INFORMES)
def test_periodo_vacio_devuelve_cero_filas(informe):
    asegurar_hechos_suscripciones()
    filas = ejecutar_suscripciones(informe, desde=VACIO, hasta=VACIO, mes="1999-01")
    assert filas == [], (
        f"'{informe}' devolvió {filas!r} en un período sin datos"
    )
