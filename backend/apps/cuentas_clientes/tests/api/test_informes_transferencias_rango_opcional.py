"""T043 — `transferencias-propiedad` es el único de los ocho con rango (FR-013).

Y la mitad que más importa es que **omitirlo no sea un error**. El resto de
listados del departamento rechazan `desde`/`hasta` con `400`; éste los acepta y
además funciona sin ellos, devolviendo el histórico completo paginado.

La asimetría es deliberada y conviene que quede fijada: una transferencia
*ocurre en un instante*, así que acotarla por período tiene sentido; una cuenta
*está* en un estado, y no lo tiene.
"""

from __future__ import annotations

import pytest

BASE = "/api/v1/informes/cuentas-clientes"
RUTA = f"{BASE}/transferencias-propiedad"


@pytest.mark.api
class TestSinRango:
    def test_es_200_no_400(self, api_client, admin_auth_headers, transferencias_sembradas):
        assert api_client.get(RUTA, **admin_auth_headers).status_code == 200

    def test_devuelve_el_historico_completo(
        self, api_client, admin_auth_headers, transferencias_sembradas
    ):
        cuerpo = api_client.get(RUTA, **admin_auth_headers).json()

        assert len(cuerpo["data"]) == 3

    def test_meta_no_declara_extremos_que_no_se_aplicaron(
        self, api_client, admin_auth_headers, transferencias_sembradas
    ):
        # `{"desde": null}` sugeriría que se filtró por una fecha nula.
        cuerpo = api_client.get(RUTA, **admin_auth_headers).json()

        assert "desde" not in cuerpo["meta"]["filtros"]
        assert "hasta" not in cuerpo["meta"]["filtros"]


@pytest.mark.api
class TestConRango:
    def test_solo_desde_acota(self, api_client, admin_auth_headers, transferencias_sembradas):
        cuerpo = api_client.get(f"{RUTA}?desde=2026-08-06", **admin_auth_headers).json()

        assert len(cuerpo["data"]) == 2

    def test_solo_hasta_acota(self, api_client, admin_auth_headers, transferencias_sembradas):
        cuerpo = api_client.get(f"{RUTA}?hasta=2026-08-06", **admin_auth_headers).json()

        assert len(cuerpo["data"]) == 2

    def test_ambos_extremos_acotan_el_intervalo(
        self, api_client, admin_auth_headers, transferencias_sembradas
    ):
        cuerpo = api_client.get(
            f"{RUTA}?desde=2026-08-02&hasta=2026-08-10", **admin_auth_headers
        ).json()

        assert len(cuerpo["data"]) == 1

    def test_hasta_es_inclusiva(
        self, api_client, admin_auth_headers, transferencias_sembradas
    ):
        # La transferencia del 2026-08-06 debe entrar cuando `hasta` es ese día.
        # Si `hasta` fuera exclusiva no saldría, y nadie lo notaría sin cuadrar
        # cifras contra otra fuente.
        cuerpo = api_client.get(
            f"{RUTA}?desde=2026-08-06&hasta=2026-08-06", **admin_auth_headers
        ).json()

        assert len(cuerpo["data"]) == 1

    def test_los_extremos_aplicados_viajan_en_meta(
        self, api_client, admin_auth_headers, transferencias_sembradas
    ):
        cuerpo = api_client.get(
            f"{RUTA}?desde=2026-08-01&hasta=2026-08-31", **admin_auth_headers
        ).json()

        assert cuerpo["meta"]["filtros"]["desde"] == "2026-08-01"
        assert cuerpo["meta"]["filtros"]["hasta"] == "2026-08-31"

    def test_rango_invertido_es_400(self, api_client, admin_auth_headers):
        respuesta = api_client.get(
            f"{RUTA}?desde=2026-08-31&hasta=2026-08-01", **admin_auth_headers
        )

        assert respuesta.status_code == 400

    def test_formato_no_iso_es_400(self, api_client, admin_auth_headers):
        assert api_client.get(f"{RUTA}?desde=ayer", **admin_auth_headers).status_code == 400

    def test_granularidad_se_rechaza_aunque_acepte_rango(
        self, api_client, admin_auth_headers
    ):
        # Acepta rango, pero sigue sin haber agrupación que granular.
        respuesta = api_client.get(f"{RUTA}?granularidad=mes", **admin_auth_headers)

        assert respuesta.status_code == 400


@pytest.mark.api
class TestLaAsimetriaConLosOtrosSiete:
    @pytest.mark.parametrize(
        "informe",
        [
            "usuarios-por-rol",
            "sesiones-activas",
            "credenciales-temporales",
            "accesos-tecnicos",
            "solicitudes-alta-pendientes",
            "onboarding-incompleto",
            "cuentas-por-estado",
        ],
    )
    def test_los_otros_siete_rechazan_el_rango(
        self, api_client, admin_auth_headers, informe
    ):
        respuesta = api_client.get(
            f"{BASE}/{informe}?desde=2026-08-01", **admin_auth_headers
        )

        assert respuesta.status_code == 400

    def test_y_este_lo_acepta(self, api_client, admin_auth_headers):
        respuesta = api_client.get(f"{RUTA}?desde=2026-08-01", **admin_auth_headers)

        assert respuesta.status_code == 200
