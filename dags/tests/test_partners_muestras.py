"""T062 — toda medida estadística declara muestras (SC-011)."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.consultas import cargar, listar  # noqa: E402

INFORMES = listar("partners")
ESTADISTICOS = ("p95", "media", "quantile", "avg(")


def columnas_de(informe: str) -> list[str]:
    cuerpo = "\n".join(
        l for l in cargar(informe, departamento="partners").splitlines()
        if not l.strip().startswith("--")
    )
    return re.findall(r"\bAS\s+([A-Za-z_][A-Za-z0-9_]*)", cuerpo)


@pytest.mark.parametrize("informe", INFORMES)
def test_si_hay_estadistico_hay_muestras(informe):
    texto = "\n".join(
        l for l in cargar(informe, departamento="partners").splitlines()
        if not l.strip().startswith("--")
    ).lower()
    if not any(e in texto for e in ESTADISTICOS):
        pytest.skip(f"'{informe}' no publica medida estadística")
    columnas = columnas_de(informe)
    assert "muestras" in columnas or "llamadas" in columnas, informe
