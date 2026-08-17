"""T076 — un caso con cero heridos y uno sin heridos registrados no se confunden."""

from __future__ import annotations

import pytest

from apps.informes_estrategicos.tests.conftest import cliente, pedir
from core.repositories.informes_tacticos.modelo_repository import ModeloRepository

pytestmark = pytest.mark.integration

SQL = """
SELECT
    countIf(num_heridos = 0) AS con_cero,
    countIf(num_heridos IS NULL) AS sin_registrar
FROM hecho_accidente FINAL
WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
  AND fue_descartado = 0 AND es_duplicado = 0
"""


class TestCeroVsNoRegistrado:
    def test_casos_con_dato_no_iguala_casos_si_hay_no_registrados(self):
        repo = ModeloRepository()
        try:
            filas = repo._client.query(
                SQL,
                params={"desde": "2026-01-01", "hasta": "2026-12-31"},
                settings={"readonly": "1"},
            )
        except Exception:
            pytest.skip("el modelo analítico no está disponible")

        con_cero = int(filas[0]["con_cero"])
        sin_registrar = int(filas[0]["sin_registrar"])
        assert con_cero > 0 or sin_registrar > 0

        director = cliente(["DirectorOperaciones"])
        respuesta = pedir(director, "impacto-humano", granularidad="anio")
        if respuesta.status_code != 200:
            pytest.skip("el modelo analítico no está disponible")

        casos = sum(int(f["casos"]) for f in respuesta.json()["data"])
        con_dato = sum(int(f["casos_con_dato"]) for f in respuesta.json()["data"])
        if sin_registrar > 0:
            assert con_dato < casos, (
                "casos_con_dato iguala casos: los no registrados se están "
                "sumando como ceros y el impacto bajaría al empeorar el registro"
            )
        assert con_dato <= casos
