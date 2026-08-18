"""T042 — ningún informe de OT06 devuelve medio de cobro."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.consultas import cargar, listar  # noqa: E402

OT06 = [n for n in listar("suscripciones") if n.startswith("ot06_")]
PROHIBIDAS = ("token", "ultimosdigitos", "idmetodopago", "tarjeta")


def cuerpo(nombre: str) -> str:
    return "\n".join(
        l for l in cargar(nombre, departamento="suscripciones").splitlines()
        if not l.strip().startswith("--")
    )


@pytest.mark.parametrize("informe", OT06)
def test_ot06_no_nombra_medio_de_cobro(informe):
    ids = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", re.sub(r"'[^']*'", " ", cuerpo(informe))))
    for ident in ids:
        bajo = ident.lower()
        for p in PROHIBIDAS:
            assert p not in bajo, f"{informe} nombra {ident}"
