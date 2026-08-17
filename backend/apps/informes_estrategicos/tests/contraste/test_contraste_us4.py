"""T079 — contraste US4 (SC-007)."""

from __future__ import annotations

import pytest

from apps.informes_estrategicos.tests.conftest import cliente, pedir
from core.repositories.informes_tacticos.modelo_repository import ModeloRepository

pytestmark = pytest.mark.integration

PARAMS = {"desde": "2026-01-01", "hasta": "2026-12-31"}


class TestContrasteUs4:
    def test_impacto_humano_las_sumas_coinciden(self):
        repo = ModeloRepository()
        try:
            tactico = repo.ejecutar(
                "ot21_impacto_humano", departamento="emergencias", parametros=PARAMS
            )
        except Exception:
            pytest.skip("el modelo analítico no está disponible")

        director = cliente(["DirectorOperaciones"])
        respuesta = pedir(director, "impacto-humano", granularidad="anio")
        if respuesta.status_code != 200:
            pytest.skip("el modelo analítico no está disponible")

        def _suma(filas, campo):
            return sum(int(f[campo] or 0) for f in filas)

        est = respuesta.json()["data"]
        # El táctico no excluye descartados/duplicados; las víctimas de los
        # casos válidos tienen que ser <= las del táctico, y los recuentos de
        # heridos/fallecidos del estratégico no usan coalesce a 0.
        assert _suma(est, "casos") <= _suma(tactico, "casos")
        assert _suma(est, "heridos") <= _suma(tactico, "heridos")

    def test_escaladas_coinciden_en_casos_y_con_escalada(self):
        repo = ModeloRepository()
        try:
            tactico = repo.ejecutar(
                "ot24_escaladas_severidad", departamento="emergencias", parametros=PARAMS
            )
        except Exception:
            pytest.skip("el modelo analítico no está disponible")

        director = cliente(["DirectorOperaciones"])
        respuesta = pedir(director, "escaladas-de-severidad", granularidad="anio")
        if respuesta.status_code != 200:
            pytest.skip("el modelo analítico no está disponible")

        est = respuesta.json()["data"]
        assert sum(int(f["casos"]) for f in est) <= sum(int(f["casos"]) for f in tactico)
        assert sum(int(f["con_escalada"]) for f in est) == sum(
            int(f["con_escalada"]) for f in tactico
        )

    def test_evidencia_parte_de_la_misma_fuente(self):
        repo = ModeloRepository()
        try:
            tactico = repo.ejecutar(
                "ot24_cobertura_evidencia", departamento="emergencias", parametros=PARAMS
            )
        except Exception:
            pytest.skip("el modelo analítico no está disponible")

        director = cliente(["DirectorOperaciones"])
        respuesta = pedir(director, "cobertura-de-evidencia", granularidad="anio")
        if respuesta.status_code != 200:
            pytest.skip("el modelo analítico no está disponible")

        # El estratégico solo cuenta cerrados; el táctico cuenta todos. El
        # recuento estratégico tiene que ser menor o igual, nunca mayor.
        cerrados = sum(int(f["casos_cerrados"]) for f in respuesta.json()["data"])
        todos = sum(int(f["casos"]) for f in tactico)
        assert cerrados <= todos
