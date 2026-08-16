"""T025 — los cuatro listados de OT18 rechazan `desde`/`hasta` con 400 (FR-012).

Son listados de **estado actual**: describen quién tiene acceso *ahora*. Un
rango de fechas no significa nada sobre ellos.

Lo que se prueba no es que el rango "no funcione", sino que **se rechace en vez
de ignorarse**. Ignorarlo devolvería `200` con el listado completo, y el
consumidor creería estar viendo un intervalo mientras ve el total — una
divergencia que solo se descubre cuadrando cifras contra otra fuente.
"""

from __future__ import annotations

import pytest

BASE = "/api/v1/informes/cuentas-clientes"

ENDPOINTS = [
    "usuarios-por-rol",
    "sesiones-activas",
    "credenciales-temporales",
    "accesos-tecnicos",
]


@pytest.mark.api
@pytest.mark.parametrize("informe", ENDPOINTS)
class TestRechazaElRango:
    def test_desde_es_400(self, api_client, admin_auth_headers, informe):
        respuesta = api_client.get(
            f"{BASE}/{informe}?desde=2026-01-01", **admin_auth_headers
        )

        assert respuesta.status_code == 400

    def test_hasta_es_400(self, api_client, admin_auth_headers, informe):
        respuesta = api_client.get(
            f"{BASE}/{informe}?hasta=2026-01-31", **admin_auth_headers
        )

        assert respuesta.status_code == 400

    def test_ambos_es_400(self, api_client, admin_auth_headers, informe):
        respuesta = api_client.get(
            f"{BASE}/{informe}?desde=2026-01-01&hasta=2026-01-31", **admin_auth_headers
        )

        assert respuesta.status_code == 400

    def test_el_error_nombra_el_parametro_sobrante(
        self, api_client, admin_auth_headers, informe
    ):
        # Sin el nombre, quien recibe el 400 no sabe qué quitar.
        cuerpo = api_client.get(
            f"{BASE}/{informe}?desde=2026-01-01", **admin_auth_headers
        ).json()

        assert cuerpo["error"] == "bad_request"
        assert "desde" in cuerpo["detail"]

    def test_granularidad_tambien_se_rechaza(
        self, api_client, admin_auth_headers, informe
    ):
        # Es de informes agregados: aquí no hay agrupación que granular.
        respuesta = api_client.get(
            f"{BASE}/{informe}?granularidad=mes", **admin_auth_headers
        )

        assert respuesta.status_code == 400

    def test_sin_rango_es_200(self, api_client, admin_auth_headers, informe):
        assert api_client.get(f"{BASE}/{informe}", **admin_auth_headers).status_code == 200
