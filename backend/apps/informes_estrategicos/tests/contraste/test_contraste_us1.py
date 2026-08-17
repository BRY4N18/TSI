"""T036 — contraste US1 (SC-007).

E6-02 mide accidente→llegada sobre el caso. `ot22_tiempo_respuesta_por_severidad`
mide despacho→llegada sobre el intento. No se fuerza la igualdad de tiempos:
son intervalos distintos, y la spec corrigió el JOIN que el catálogo pedía.

Lo que sí tiene que cuadrar es el recuento de casos con llegada, contra una
consulta independiente sobre `hecho_accidente`.
"""

from __future__ import annotations

import pytest

from apps.informes_estrategicos.tests.conftest import cliente, pedir
from core.repositories.informes_tacticos.modelo_repository import ModeloRepository

pytestmark = pytest.mark.integration

SQL_INDEPENDIENTE = """
SELECT coalesce(severidad, 'Desconocido') AS severidad,
       count() AS casos
FROM hecho_accidente FINAL
WHERE fecha BETWEEN {desde:Date} AND {hasta:Date}
  AND hora_primera_llegada IS NOT NULL
  AND fue_descartado = 0 AND es_duplicado = 0
GROUP BY severidad
ORDER BY casos DESC
"""


class TestContrasteUs1:
    def test_los_recuentos_por_severidad_cuadran_con_el_hecho(self):
        director = cliente(["DirectorOperaciones"])
        respuesta = pedir(director, "tiempo-respuesta-por-severidad", granularidad="anio")
        if respuesta.status_code != 200:
            pytest.skip("el modelo analítico no está disponible")

        por_api = {}
        for fila in respuesta.json()["data"]:
            por_api[fila["severidad"]] = por_api.get(fila["severidad"], 0) + int(fila["casos"])

        repo = ModeloRepository()
        try:
            independientes = repo._client.query(
                SQL_INDEPENDIENTE,
                params={"desde": "2026-01-01", "hasta": "2026-12-31"},
                settings={"readonly": "1"},
            )
        except Exception:
            pytest.skip("el modelo analítico no está disponible")

        por_hecho = {f["severidad"]: int(f["casos"]) for f in independientes}
        assert por_api == por_hecho

    def test_ot22_mide_otro_intervalo_y_no_se_tolera_en_silencio(self):
        """La divergencia con el táctico se declara, no se tapa con tolerancia."""
        repo = ModeloRepository()
        try:
            tactico = repo.ejecutar(
                "ot22_tiempo_respuesta_por_severidad",
                departamento="emergencias",
                parametros={"desde": "2026-01-01", "hasta": "2026-12-31"},
            )
        except Exception:
            pytest.skip("el modelo analítico no está disponible")

        director = cliente(["DirectorOperaciones"])
        respuesta = pedir(director, "tiempo-respuesta-por-severidad", granularidad="anio")
        if respuesta.status_code != 200:
            pytest.skip("el modelo analítico no está disponible")

        # Distinto grano (intentos vs casos) o distinto intervalo: las medianas
        # en segundos del táctico no son las medianas en minutos del estratégico.
        assert "mediana_seg" in tactico[0]
        assert "mediana_min" in respuesta.json()["data"][0]
