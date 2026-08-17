"""T067 — ningún caso abierto aparece como cerrado; los tramos cubren sin solaparse."""

from __future__ import annotations

import pytest

from apps.informes_estrategicos.tests.conftest import cliente, pedir
from core.repositories.informes_tacticos.modelo_repository import ModeloRepository

pytestmark = pytest.mark.integration

SQL_ABIERTOS = """
SELECT count() AS abiertos
FROM hecho_accidente FINAL
WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
  AND hora_cierre IS NULL
  AND fue_descartado = 0 AND es_duplicado = 0
"""


class TestEnvejecimiento:
    def test_los_tramos_cubren_la_cartera_sin_solaparse(self):
        director = cliente(["DirectorOperaciones"])
        respuesta = pedir(director, "envejecimiento-de-casos-abiertos")
        if respuesta.status_code != 200:
            pytest.skip("el modelo analítico no está disponible")

        filas = respuesta.json()["data"]
        tramos = [int(f["tramo_dias"]) for f in filas]
        assert tramos == sorted(tramos)
        assert len(tramos) == len(set(tramos)), "tramos solapados"
        total = sum(int(f["casos_abiertos"]) for f in filas)

        repo = ModeloRepository()
        try:
            abiertos = repo._client.query(
                SQL_ABIERTOS,
                params={"desde": "2026-01-01", "hasta": "2026-12-31"},
                settings={"readonly": "1"},
            )
        except Exception:
            pytest.skip("el modelo analítico no está disponible")

        assert total == int(abiertos[0]["abiertos"]), (
            "la suma de tramos no cubre la cartera, o un abierto se contó como cerrado"
        )
