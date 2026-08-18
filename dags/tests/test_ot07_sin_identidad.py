"""T056 — OT07 no devuelve identidad del administrador."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.consultas import cargar, listar  # noqa: E402

OT07 = [n for n in listar("suscripciones") if n.startswith("ot07_")]
PROHIBIDAS = ("idadmin", "idadminaprobador", "motivo_rechazo")


@pytest.mark.parametrize("informe", OT07)
def test_ot07_sin_identidad(informe):
    texto = cargar(informe, departamento="suscripciones")
    ids = {i.lower() for i in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", texto)}
    for p in PROHIBIDAS:
        assert p not in ids, f"{informe} nombra {p}"
