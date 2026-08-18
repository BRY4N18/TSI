"""T059 — un período vacío devuelve cero filas, no una fila de ceros (FR-031)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.consultas import listar  # noqa: E402

from tests.almacen import (  # noqa: E402
    asegurar_hechos_ventas_crm,
    ejecutar_ventas_crm,
    requiere_modelo,
)

INFORMES = listar("ventas_crm")
#: Antes de cualquier `fecha_registro` del origen (minimo observado: 2026-07).
#: 2098 no sirve: permanencia y pipeline son un corte sobre `dim_prospecto`,
#: y un `hasta` posterior al registro sigue viendo a esos prospectos.
VACIO = "1999-01-01"


@requiere_modelo
@pytest.mark.parametrize("informe", INFORMES)
def test_periodo_vacio_devuelve_cero_filas(informe):
    asegurar_hechos_ventas_crm()
    filas = ejecutar_ventas_crm(informe, desde=VACIO, hasta=VACIO)
    assert filas == [], (
        f"'{informe}' devolvio {filas!r} en un periodo sin datos: una fila de "
        f"ceros afirma que se midio y salio cero, que no es lo mismo"
    )
