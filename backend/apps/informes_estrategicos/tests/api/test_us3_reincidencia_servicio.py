"""Reincidencia agrupa cliente × servicio."""

from __future__ import annotations

from pathlib import Path

SQL = (
    Path(__file__).resolve().parents[5]
    / "dags/lib/consultas/estrategicos/oe5/e5_08_reincidencia_soporte.sql"
)


def test_us3_sql_agrupa_cliente_y_servicio():
    texto = SQL.read_text(encoding="utf-8")
    assert "idcliente" in texto
    assert "servicio" in texto
    assert "GROUP BY periodo, idcliente, servicio" in texto
