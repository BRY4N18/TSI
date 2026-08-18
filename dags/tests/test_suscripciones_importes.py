"""T065 — todo importe declara moneda y periodicidad (FR-036)."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.consultas import cargar, listar  # noqa: E402

CON_IMPORTE = (
    "ot06_mrr",
    "ot06_ingresos",
    "ot07_movimientos_plan",
    "ot07_nrr",
    "ot05_distribucion_cartera",
)


@pytest.mark.parametrize("informe", CON_IMPORTE)
def test_el_importe_declara_moneda_y_periodicidad(informe):
    texto = cargar(informe, departamento="suscripciones")
    ids = {i.lower() for i in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", texto)}
    assert "moneda" in ids, f"{informe} no declara moneda"
    assert "periodicidad" in ids, f"{informe} no declara periodicidad"


def test_el_catalogo_sigue_teniendo_trece():
    assert len(listar("suscripciones")) == 13
