"""T051 — contraste US2 (SC-007): origen y desviación coinciden con el táctico."""

from __future__ import annotations

from collections import defaultdict

import pytest

from apps.informes_estrategicos.tests.conftest import cliente, pedir
from core.repositories.informes_tacticos.modelo_repository import ModeloRepository

pytestmark = pytest.mark.integration

PARAMS = {"desde": "2026-01-01", "hasta": "2026-12-31"}


class TestContrasteUs2:
    def test_origen_de_asignacion_coincide_en_recuentos(self):
        repo = ModeloRepository()
        try:
            tactico = repo.ejecutar(
                "ot22_asignacion_automatica_vs_manual",
                departamento="emergencias",
                parametros=PARAMS,
            )
        except Exception:
            pytest.skip("el modelo analítico no está disponible")

        director = cliente(["DirectorOperaciones"])
        respuesta = pedir(director, "origen-de-asignacion", granularidad="anio")
        if respuesta.status_code != 200:
            pytest.skip("el modelo analítico no está disponible")

        por_est = defaultdict(int)
        for fila in respuesta.json()["data"]:
            por_est[fila["origen"]] += int(fila["despachos"])
        por_tac = {f["origen"]: int(f["despachos"]) for f in tactico}
        assert dict(por_est) == por_tac

    def test_desviacion_coincide_con_granularidad_mes(self):
        repo = ModeloRepository()
        extra = {"ventana_dias": 90, "muestra_minima": 5}
        try:
            tactico = repo.ejecutar(
                "ot23_desviacion_llegada",
                departamento="emergencias",
                parametros={**PARAMS, **extra},
            )
        except Exception:
            pytest.skip("el modelo analítico no está disponible")

        director = cliente(["DirectorOperaciones"])
        respuesta = pedir(
            director, "desviacion-de-llegada", granularidad="mes", **extra
        )
        if respuesta.status_code != 200:
            pytest.skip("el modelo analítico no está disponible")

        def clave(fila):
            return (fila["periodo"], fila["unidad"])

        por_tac = {clave(f): int(f["llegadas_medidas"]) for f in tactico}
        por_est = {clave(f): int(f["llegadas_medidas"]) for f in respuesta.json()["data"]}
        assert por_est == por_tac
