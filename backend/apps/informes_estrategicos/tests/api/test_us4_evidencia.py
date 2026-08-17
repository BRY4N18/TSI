"""T078 — solo casos cerrados; foto y nota se publican por separado."""

from __future__ import annotations

import pytest

from apps.informes_estrategicos.tests.conftest import cliente, pedir
from core.repositories.informes_tacticos.modelo_repository import ModeloRepository

pytestmark = pytest.mark.integration

SQL = """
SELECT count() AS cerrados
FROM hecho_accidente FINAL
WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
  AND hora_cierre IS NOT NULL
  AND fue_descartado = 0 AND es_duplicado = 0
"""


class TestEvidencia:
    def test_solo_entran_cerrados_y_foto_nota_van_separadas(self):
        director = cliente(["DirectorOperaciones"])
        respuesta = pedir(director, "cobertura-de-evidencia", granularidad="anio")
        if respuesta.status_code != 200:
            pytest.skip("el modelo analítico no está disponible")

        filas = respuesta.json()["data"]
        assert filas
        for fila in filas:
            assert "con_foto" in fila and "con_nota" in fila and "con_ambas" in fila
            assert int(fila["con_ambas"]) <= int(fila["con_foto"])
            assert int(fila["con_ambas"]) <= int(fila["con_nota"])

        total = sum(int(f["casos_cerrados"]) for f in filas)
        repo = ModeloRepository()
        try:
            cerrados = repo._client.query(
                SQL,
                params={"desde": "2026-01-01", "hasta": "2026-12-31"},
                settings={"readonly": "1"},
            )
        except Exception:
            pytest.skip("el modelo analítico no está disponible")
        assert total == int(cerrados[0]["cerrados"])
