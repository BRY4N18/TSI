"""T032 — `facturas` acepta rango **opcional** (FR-016).

Es el único de los cuatro listados del departamento que lo acepta: una factura
se emite en un instante, mientras que una suscripción, un medio de cobro y una
solicitud *están* en un estado.

Y omitirlo **no es un error**: devuelve el histórico completo paginado.
"""

from __future__ import annotations

import pytest

BASE = "/api/v1/informes/suscripciones-facturacion"
RUTA = f"{BASE}/facturas"


@pytest.mark.api
class TestSinRango:
    def test_es_200_no_400(self, api_client, admin_auth_headers, facturas_sembradas):
        assert api_client.get(RUTA, **admin_auth_headers).status_code == 200

    def test_devuelve_el_historico_completo(
        self, api_client, admin_auth_headers, facturas_sembradas
    ):
        cuerpo = api_client.get(f"{RUTA}?limit=500", **admin_auth_headers).json()

        assert len(cuerpo["data"]) == 4

    def test_meta_no_declara_extremos_que_no_se_aplicaron(
        self, api_client, admin_auth_headers, facturas_sembradas
    ):
        cuerpo = api_client.get(RUTA, **admin_auth_headers).json()

        assert "desde" not in cuerpo["meta"]["filtros"]
        assert "hasta" not in cuerpo["meta"]["filtros"]


@pytest.mark.api
class TestConRango:
    def test_solo_desde_acota(self, api_client, admin_auth_headers, facturas_sembradas):
        # Emitidas: hace 40, 20, 5 y 2 días desde 2026-08-11.
        cuerpo = api_client.get(
            f"{RUTA}?desde=2026-08-01&limit=500", **admin_auth_headers
        ).json()

        assert len(cuerpo["data"]) == 2

    def test_solo_hasta_acota(self, api_client, admin_auth_headers, facturas_sembradas):
        cuerpo = api_client.get(
            f"{RUTA}?hasta=2026-08-01&limit=500", **admin_auth_headers
        ).json()

        assert len(cuerpo["data"]) == 2

    def test_ambos_extremos_acotan(
        self, api_client, admin_auth_headers, facturas_sembradas
    ):
        # Emitidas el 2026-07-02 y el 2026-07-22: las dos caen dentro.
        cuerpo = api_client.get(
            f"{RUTA}?desde=2026-07-01&hasta=2026-08-01&limit=500", **admin_auth_headers
        ).json()

        assert len(cuerpo["data"]) == 2

    def test_un_intervalo_estrecho_deja_una_sola(
        self, api_client, admin_auth_headers, facturas_sembradas
    ):
        cuerpo = api_client.get(
            f"{RUTA}?desde=2026-07-10&hasta=2026-08-01&limit=500", **admin_auth_headers
        ).json()

        assert len(cuerpo["data"]) == 1

    def test_los_extremos_aplicados_viajan_en_meta(
        self, api_client, admin_auth_headers, facturas_sembradas
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


@pytest.mark.api
class TestLosOtrosTresNoLoAceptan:
    @pytest.mark.parametrize(
        "informe", ["suscripciones", "metodos-pago", "solicitudes-cambio-plan"]
    )
    def test_rechazan_el_rango_generico(self, api_client, admin_auth_headers, informe):
        respuesta = api_client.get(
            f"{BASE}/{informe}?desde=2026-08-01", **admin_auth_headers
        )

        assert respuesta.status_code == 400

    def test_pero_suscripciones_si_acepta_el_rango_de_cancelacion(
        self, api_client, admin_auth_headers, dos_cuentas
    ):
        """No es el período del contrato: es un filtro **de columna**."""
        respuesta = api_client.get(
            f"{BASE}/suscripciones?cancelada_desde=2026-07-01", **admin_auth_headers
        )

        assert respuesta.status_code == 200

    def test_el_rango_de_cancelacion_acota_de_verdad(
        self, api_client, admin_auth_headers, dos_cuentas
    ):
        con = api_client.get(
            f"{BASE}/suscripciones?cancelada_desde=2026-07-01&limit=500",
            **admin_auth_headers,
        ).json()
        sin = api_client.get(
            f"{BASE}/suscripciones?limit=500", **admin_auth_headers
        ).json()

        assert len(con["data"]) < len(sin["data"])
