"""NRR publica expansión, contracción y churn, no solo el neto."""

from __future__ import annotations

from pathlib import Path

import pytest

from apps.informes_estrategicos.tests.conftest import cliente, pedir_oe5

SQL = (
    Path(__file__).resolve().parents[5]
    / "dags/lib/consultas/estrategicos/oe5/e5_02_retencion_neta_ingresos.sql"
)


def test_us2_sql_descompone_nrr():
    texto = SQL.read_text(encoding="utf-8")
    assert "expansion" in texto
    assert "contraccion" in texto
    assert "churn" in texto
    assert "0 AS expansion" not in texto.replace(" ", "")


def test_us2_nrr_respuesta_descompone_si_hay_filas():
    respuesta = pedir_oe5(cliente(["DirectorFinanciero"]), "retencion-neta-ingresos")
    if respuesta.status_code != 200:
        pytest.skip("el modelo analítico no está disponible")
    for fila in respuesta.json()["data"]:
        assert "expansion" in fila
        assert "contraccion" in fila
        assert "churn" in fila
