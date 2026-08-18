"""Ninguna consulta OE5 nombra calificación de cierre de accidente."""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[5] / "dags"))

from lib.consultas import cargar, listar  # noqa: E402

DEPARTAMENTO = "estrategicos/oe5"


def test_us4_sql_sin_calificacion_de_cierre():
    for nombre in listar(DEPARTAMENTO):
        sql = cargar(nombre, departamento=DEPARTAMENTO)
        ids = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", sql))
        assert "calificacion" not in ids, nombre
        assert "hecho_cierre_accidente" not in sql.lower()
