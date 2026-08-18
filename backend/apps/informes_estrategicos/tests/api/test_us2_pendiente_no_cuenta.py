"""Un movimiento pendiente no entra al ingreso."""

from __future__ import annotations

from pathlib import Path

SQL = (
    Path(__file__).resolve().parents[5]
    / "dags/lib/consultas/estrategicos/oe5/e5_03_movimientos_de_plan.sql"
)


def test_us2_sql_solo_aprobada_o_aplicada():
    texto = SQL.read_text(encoding="utf-8")
    assert "aprobada" in texto
    assert "aplicada" in texto
    assert "pendiente" not in texto
    cuerpo = "\n".join(
        l for l in texto.splitlines() if not l.strip().startswith("--")
    )
    assert "dim_plan" not in cuerpo
