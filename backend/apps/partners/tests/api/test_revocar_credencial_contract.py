"""Contrato de `POST /credenciales/{id}/revocar` (T013, T015, T018).

Escenario A del quickstart, mas los rechazos y la restriccion de autenticacion.
"""

from __future__ import annotations

import pytest

from conftest import PINOT_STORE

pytestmark = [pytest.mark.django_db, pytest.mark.api]

URL = "/api/v1/credenciales/101/revocar"
CUERPO = {"motivo": "credencial expuesta en repositorio público"}


class TestCaminoFeliz:
    def test_devuelve_200_con_la_revocada_y_el_reemplazo(
        self, api_client, partner_con_credenciales, partner_auth_headers
    ):
        # Act
        respuesta = api_client.post(
            URL, CUERPO, format="json", **partner_auth_headers
        )

        # Assert
        assert respuesta.status_code == 200
        data = respuesta.json()["data"]
        assert data["revocada"]["idcredencial"] == 101
        assert data["revocada"]["activo"] is False
        assert data["reemplazo"]["nombre_credencial"] == "plataforma-siniestros"

    def test_el_secreto_del_reemplazo_aparece_una_sola_vez(
        self, api_client, partner_con_credenciales, partner_auth_headers
    ):
        # Act
        data = api_client.post(
            URL, CUERPO, format="json", **partner_auth_headers
        ).json()["data"]

        # Assert
        assert data["reemplazo"]["client_secret"]
        assert data["reemplazo"]["client_id"].startswith("tsi-p1-c")
        # El hash NUNCA sale en la respuesta.
        assert "client_secret_hash" not in data["reemplazo"]

    def test_informa_de_cuantas_credenciales_quedan_intactas(
        self, api_client, partner_con_credenciales, partner_auth_headers
    ):
        """El partner acaba de tocar seguridad: necesita ver que no se quedó
        sin servicio (RF-O55.2)."""
        # Act
        data = api_client.post(
            URL, CUERPO, format="json", **partner_auth_headers
        ).json()["data"]

        # Assert — la 102 sigue activa; la 103 estaba revocada de antes
        assert data["credenciales_intactas"] == 1


class TestRechazos:
    def test_sin_autenticacion_returns_401(self, api_client, partner_con_credenciales):
        assert api_client.post(URL, CUERPO, format="json").status_code == 401

    def test_una_credencial_de_API_no_puede_revocar(
        self, api_client, partner_con_credenciales, credencial_produccion_headers
    ):
        """🎯 T018 — si se pudiera, el atacante que ya robó una credencial
        podría revocar las demás del partner: le estaríamos dando la herramienta
        de sabotaje (`research.md` Decision 1)."""
        # Act
        respuesta = api_client.post(
            URL, CUERPO, format="json", **credencial_produccion_headers
        )

        # Assert
        assert respuesta.status_code in (401, 403)
        assert next(
            c for c in PINOT_STORE["Dim_CredencialAPI"] if c["idcredencial"] == 101
        )["activo"] is True

    def test_credencial_de_otro_partner_returns_403_sin_modificar_nada(
        self, api_client, partner_con_credenciales, partner_ajeno_auth_headers
    ):
        """CA-PAC-004 — escenario C."""
        # Act
        respuesta = api_client.post(
            URL, CUERPO, format="json", **partner_ajeno_auth_headers
        )

        # Assert
        assert respuesta.status_code == 403
        assert next(
            c for c in PINOT_STORE["Dim_CredencialAPI"] if c["idcredencial"] == 101
        )["activo"] is True

    def test_credencial_ya_inactiva_returns_409(
        self, api_client, partner_con_credenciales, partner_auth_headers
    ):
        """CA-PAC-005 — escenario D."""
        # Act
        respuesta = api_client.post(
            "/api/v1/credenciales/103/revocar", CUERPO, format="json",
            **partner_auth_headers,
        )

        # Assert
        assert respuesta.status_code == 409
        assert respuesta.json()["code"] == "credencial_inactiva"

    def test_motivo_vacio_returns_400(
        self, api_client, partner_con_credenciales, partner_auth_headers
    ):
        # Act
        respuesta = api_client.post(
            URL, {"motivo": "   "}, format="json", **partner_auth_headers
        )

        # Assert
        assert respuesta.status_code == 400

    def test_credencial_inexistente_returns_404(
        self, api_client, partner_con_credenciales, partner_auth_headers
    ):
        assert api_client.post(
            "/api/v1/credenciales/9999/revocar", CUERPO, format="json",
            **partner_auth_headers,
        ).status_code == 404


class TestIdempotencia:
    def test_el_reintento_con_la_misma_clave_no_revoca_dos_veces(
        self, api_client, partner_con_credenciales, partner_auth_headers
    ):
        """Sin esto, un timeout de red emitiría un reemplazo de más y perdería
        el secreto del primero para siempre (`idempotency.py`)."""
        # Arrange
        cabeceras = {**partner_auth_headers, "HTTP_IDEMPOTENCY_KEY": "clave-fija"}

        # Act
        primera = api_client.post(URL, CUERPO, format="json", **cabeceras)
        segunda = api_client.post(URL, CUERPO, format="json", **cabeceras)

        # Assert — misma respuesta, mismo secreto, un solo efecto
        assert primera.status_code == segunda.status_code == 200
        assert (
            primera.json()["data"]["reemplazo"]["client_secret"]
            == segunda.json()["data"]["reemplazo"]["client_secret"]
        )
