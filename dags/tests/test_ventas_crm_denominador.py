"""T058 — todo porcentaje viene con su denominador (FR-030)."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.consultas import cargar, listar  # noqa: E402

INFORMES = listar("ventas_crm")
PORCENTAJES = ("pct", "pct_paso", "pct_conversion", "tasa_acierto")


def cuerpo(nombre: str) -> str:
    return "\n".join(
        l for l in cargar(nombre, departamento="ventas_crm").splitlines()
        if not l.strip().startswith("--")
    )


@pytest.mark.parametrize("informe", INFORMES)
def test_si_hay_porcentaje_hay_denominador(informe):
    texto = cuerpo(informe)
    aliases = set(re.findall(r"\bAS\s+(\w+)", texto, flags=re.IGNORECASE))
    if not any(p in aliases for p in PORCENTAJES):
        pytest.skip(f"'{informe}' no publica porcentaje")
    assert "denominador" in aliases, (
        f"'{informe}' publica un porcentaje sin denominador: la cifra no es "
        f"comprobable"
    )
