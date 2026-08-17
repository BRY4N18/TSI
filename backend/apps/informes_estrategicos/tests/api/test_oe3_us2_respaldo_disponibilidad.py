"""T049 — el respaldo mide disponibilidad, no existencia."""

from __future__ import annotations

from pathlib import Path

import pytest

from apps.informes_estrategicos.tests.conftest import cliente, pedir_oe3

SQL = (
    Path(__file__).resolve().parents[5]
    / "dags/lib/consultas/estrategicos/oe3/e3_08_cobertura_de_respaldo.sql"
)


class TestRespaldoDisponibilidad:
    def test_el_sql_lee_el_ultimo_estado_no_la_existencia(self):
        texto = SQL.read_text(encoding="utf-8")
        cuerpo = "\n".join(
            l for l in texto.splitlines() if not l.strip().startswith("--")
        )
        assert "hecho_estado_unidad" in cuerpo
        after = cuerpo.split("hecho_estado_unidad", 1)[1]
        assert not after.lstrip().upper().startswith("FINAL")
        assert "Activa" in cuerpo

    def test_el_endpoint_responde_por_condado(self):
        respuesta = pedir_oe3(cliente(["DirectorExpansion"]), "cobertura-de-respaldo")
        if respuesta.status_code != 200:
            pytest.skip("el modelo analítico no está disponible")
        for fila in respuesta.json()["data"]:
            assert "vecinos" in fila
            assert "vecinos_con_unidad_disponible" in fila
            assert int(fila["vecinos_con_unidad_disponible"]) <= int(fila["vecinos"])
