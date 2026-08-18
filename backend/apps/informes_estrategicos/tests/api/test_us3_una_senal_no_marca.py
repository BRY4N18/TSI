"""Una sola señal no marca la cuenta."""

from __future__ import annotations

from pathlib import Path

SQL = (
    Path(__file__).resolve().parents[5]
    / "dags/lib/consultas/estrategicos/oe5/e5_12_cuentas_en_riesgo.sql"
)


def test_us3_sql_exige_dos_senales():
    texto = SQL.read_text(encoding="utf-8")
    assert "n_senales >= 2" in texto
    assert "senal_api" in texto
    assert "senal_tickets" in texto
    assert "senal_cobro" in texto
    assert "senal_sesiones" in texto
