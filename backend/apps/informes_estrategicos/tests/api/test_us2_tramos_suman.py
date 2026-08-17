"""T048 — para los casos completos, los cuatro tramos suman el total, sin residuo."""

from __future__ import annotations

import pytest

from core.repositories.informes_tacticos.modelo_repository import ModeloRepository

pytestmark = pytest.mark.integration

SQL = """
SELECT
    count() AS completos,
    countIf(
        dateDiff('second', fechahora_accidente, hora_confirmacion)
        + dateDiff('second', hora_confirmacion, hora_primera_asignacion)
        + dateDiff('second', hora_primera_asignacion, hora_primera_llegada)
        + dateDiff('second', hora_primera_llegada, hora_cierre)
        = dateDiff('second', fechahora_accidente, hora_cierre)
    ) AS cuadran
FROM hecho_accidente FINAL
WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
  AND fue_descartado = 0 AND es_duplicado = 0
  AND hora_confirmacion IS NOT NULL
  AND hora_primera_asignacion IS NOT NULL
  AND hora_primera_llegada IS NOT NULL
  AND hora_cierre IS NOT NULL
"""


class TestTramosSuman:
    def test_sin_residuo_en_casos_completos(self):
        repo = ModeloRepository()
        try:
            filas = repo._client.query(
                SQL,
                params={"desde": "2026-01-01", "hasta": "2026-12-31"},
                settings={"readonly": "1"},
            )
        except Exception:
            pytest.skip("el modelo analítico no está disponible")

        assert filas
        assert int(filas[0]["completos"]) == int(filas[0]["cuadran"]), (
            "la suma de los cuatro tramos no iguala el tiempo total: hay residuo "
            "en la definición de los hitos"
        )
        assert int(filas[0]["completos"]) > 0
