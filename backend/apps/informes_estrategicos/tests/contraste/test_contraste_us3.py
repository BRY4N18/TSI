"""T068 — contraste US3 (SC-007).

Abortos y envejecimiento coinciden con el catálogo táctico. Rechazo-y-timeout
**debe divergir** del endpoint operativo: el estratégico corrige #34 y da una
tasa mayor. La divergencia se declara, no se tolera.
"""

from __future__ import annotations

import pytest
from rest_framework.test import APIClient

from apps.informes_estrategicos.tests.conftest import cliente, pedir
from core.jwt_utils import create_access_token
from core.repositories.informes_tacticos.modelo_repository import ModeloRepository

pytestmark = pytest.mark.integration

PARAMS = {"desde": "2026-01-01", "hasta": "2026-12-31"}


def _admin():
    api = APIClient()
    api.credentials(
        HTTP_AUTHORIZATION=f"Bearer {create_access_token(user_id=1, roles=['Administrador'], session_id=1)}"
    )
    return api


class TestContrasteUs3:
    def test_abortos_coinciden_con_el_catalogo_tactico(self):
        repo = ModeloRepository()
        try:
            tactico = repo.ejecutar(
                "ot23_abortos_perdidas", departamento="emergencias", parametros=PARAMS
            )
        except Exception:
            pytest.skip("el modelo analítico no está disponible")

        director = cliente(["DirectorOperaciones"])
        respuesta = pedir(director, "abortos-y-misiones-fallidas", granularidad="anio")
        if respuesta.status_code != 200:
            pytest.skip("el modelo analítico no está disponible")

        abortados_est = sum(
            int(f["misiones_causa"])
            for f in respuesta.json()["data"]
            if f["causa"] == "abortado"
        )
        abortados_tac = int(tactico[0]["abortados"])
        assert abortados_est == abortados_tac

    def test_envejecimiento_cubre_los_mismos_abiertos(self):
        repo = ModeloRepository()
        try:
            tactico = repo.ejecutar(
                "ot25_envejecimiento_cartera",
                departamento="emergencias",
                parametros={**PARAMS, "tramos_dias": "1,3,7,30"},
            )
        except Exception:
            pytest.skip("el modelo analítico no está disponible")

        director = cliente(["DirectorOperaciones"])
        respuesta = pedir(director, "envejecimiento-de-casos-abiertos")
        if respuesta.status_code != 200:
            pytest.skip("el modelo analítico no está disponible")

        total_est = sum(int(f["casos_abiertos"]) for f in respuesta.json()["data"])
        total_tac = sum(int(f["casos_abiertos"]) for f in tactico)
        assert total_est == total_tac, (
            "el estratégico y el táctico no cubren la misma cartera de abiertos"
        )

    # `test_rechazo_diverge_del_endpoint_operativo_porque_corrige_34` se retiró
    # el 2026-08-19 junto con el endpoint que contrastaba.
    #
    # Comparaba la tasa estratégica contra
    # `informes-tacticos/despacho/rechazo-timeout-por-unidad` para demostrar que
    # el estratégico **corrige** la decisión #34: el táctico dividía por
    # transiciones de estado en vez de por intentos de despacho, así que una
    # unidad que se comportaba mejor podía salir peor.
    #
    # Ese endpoint ya no existe —los tres informes agregados se retiraron—, así
    # que la prueba no podía volver a ejecutarse: se saltaba sola y quedaba en
    # verde sin comprobar nada, que es peor que no tenerla. El defecto que
    # documentaba desapareció con el endpoint que lo contenía.

