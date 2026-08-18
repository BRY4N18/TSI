"""Tickets sin compromiso no entran en el denominador del SLA."""

from __future__ import annotations

from pathlib import Path

SQL = (
    Path(__file__).resolve().parents[5]
    / "dags/lib/consultas/estrategicos/oe5/e5_04_cumplimiento_sla.sql"
)


def test_us1_sla_sql_filtra_compromiso():
    texto = SQL.read_text(encoding="utf-8")
    assert "tiene_compromiso" in texto
    assert "con_compromiso" in texto
    assert "sin_compromiso" in texto
    assert "HAVING con_compromiso > 0" in texto
