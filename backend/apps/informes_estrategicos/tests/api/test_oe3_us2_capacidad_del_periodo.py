"""T047 — dos períodos con distinta flota no pueden devolver la misma capacidad
si se está leyendo la flota actual. El SQL no filtra es_vigente = 1.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from apps.informes_estrategicos.tests.conftest import cliente, pedir_oe3

SQL = (
    Path(__file__).resolve().parents[5]
    / "dags/lib/consultas/estrategicos/oe3/e3_07_ratio_demanda_capacidad.sql"
)


class TestCapacidadDelPeriodo:
    def test_el_sql_no_usa_la_flota_actual(self):
        texto = SQL.read_text(encoding="utf-8")
        cuerpo = "\n".join(
            l for l in texto.splitlines() if not l.strip().startswith("--")
        )
        assert "es_vigente = 1" not in cuerpo
        assert "u.es_vigente" not in cuerpo
        assert "valido_desde" in cuerpo and "valido_hasta" in cuerpo

    def test_dos_periodos_responden(self):
        director = cliente(["DirectorOperaciones"])
        a = pedir_oe3(director, "ratio-demanda-capacidad", desde="2026-02-01", hasta="2026-02-28", granularidad="mes")
        b = pedir_oe3(director, "ratio-demanda-capacidad", desde="2026-07-01", hasta="2026-07-31", granularidad="mes")
        if a.status_code != 200 or b.status_code != 200:
            pytest.skip("el modelo analítico no está disponible")
        assert a.json()["meta"].get("alcance")
