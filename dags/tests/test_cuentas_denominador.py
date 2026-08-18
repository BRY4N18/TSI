"""T062 — todo porcentaje viene con su denominador."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.consultas import cargar, listar  # noqa: E402

INFORMES = listar("cuentas")

NUMERADORES = {
    "ot17_churn_por_cohorte": {"pct_churn": "bajas"},
    "ot17_usuarios_vs_tope": {
        "pct_ocupacion": "usuarios_conocidos",
        "pct_cobertura_pertenencia": "usuarios_conocidos",
    },
    "ot04_embudo_abandono": {"pct_supera": "clientes_que_llegaron"},
    "ot04_tasa_aprobacion": {"pct": "aprobadas"},
}

DENOMINADORES = {
    "ot17_churn_por_cohorte": {"pct_churn": "clientes_iniciales"},
    "ot17_usuarios_vs_tope": {
        "pct_ocupacion": "tope_plan",
        "pct_cobertura_pertenencia": "usuarios_conocidos",
    },
    "ot04_embudo_abandono": {"pct_supera": "clientes_que_llegaron"},
    "ot04_tasa_aprobacion": {"pct": "solicitudes"},
}


def columnas_de(informe: str) -> list[str]:
    cuerpo = "\n".join(
        l for l in cargar(informe, departamento="cuentas").splitlines()
        if not l.strip().startswith("--")
    )
    return re.findall(r"\bAS\s+([A-Za-z_][A-Za-z0-9_]*)", cuerpo)


@pytest.mark.parametrize("informe", INFORMES)
def test_todo_porcentaje_lleva_numerador_y_denominador(informe):
    columnas = columnas_de(informe)
    porcentajes = [c for c in columnas if c.startswith("pct")]
    if not porcentajes:
        pytest.skip(f"'{informe}' no publica ningún porcentaje")

    declarados = NUMERADORES.get(informe)
    denoms = DENOMINADORES.get(informe)
    assert declarados is not None, (
        f"'{informe}' publica {porcentajes} y no está en NUMERADORES"
    )
    for pct in porcentajes:
        assert declarados.get(pct) in columnas, pct
        assert denoms.get(pct) in columnas, pct
