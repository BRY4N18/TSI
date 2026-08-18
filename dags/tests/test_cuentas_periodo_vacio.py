"""T061 — un período sin datos devuelve cero filas, no una fila de ceros."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.consultas import listar  # noqa: E402

from tests.almacen import asegurar_hechos_cuentas, ejecutar_cuentas, requiere_modelo  # noqa: E402

INFORMES = [i for i in listar("cuentas") if i != "ot04_embudo_abandono"]
VACIO = "1999-01-01"


@requiere_modelo
@pytest.mark.parametrize("informe", INFORMES)
def test_periodo_vacio_devuelve_cero_filas(informe):
    asegurar_hechos_cuentas()
    from tests.almacen import limpiar_cuentas

    limpiar_cuentas()
    filas = ejecutar_cuentas(
        informe,
        desde=VACIO,
        hasta=VACIO,
        mes_cohorte="1999-01",
        pares="",
    )
    assert filas == [], (
        f"'{informe}' devolvió {filas!r} en un período sin datos"
    )
