"""T037 — ningún informe de OT09 devuelve IP."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.consultas import cargar, listar  # noqa: E402

OT09 = [i for i in listar("partners") if i.startswith("ot09_")]


@pytest.mark.parametrize("informe", OT09)
def test_ot09_no_nombra_ip(informe):
    texto = "\n".join(
        l for l in cargar(informe, departamento="partners").splitlines()
        if not l.strip().startswith("--")
    ).lower()
    ids = set(re.findall(r"[a-z_][a-z0-9_]*", re.sub(r"'[^']*'", " ", texto)))
    assert "iporigen" not in ids
    assert "ip" not in ids
