"""Contrato de suspension y reactivacion manual (T023, T024, T028).

Escenarios K y L, y el control de rol: **solo Administrador** en las dos.
"""

from __future__ import annotations

import pytest

from conftest import PINOT_STORE

pytestmark = [pytest.mark.django_db, pytest.mark.api]

SUSPENDER = "/api/v1/partners/1/suspender"
REACTIVAR = "/api/v1/partners/1/reactivar"


class TestSuspender:
    def test_suspende_con_cascada_y_devuelve_el_recuento(
        self, api_client, partner_con_credenciales, admin_auth_headers
    ):
        # Act
        respuesta = api_client.post(
            SUSPENDER, {"motivo": "contrato vencido"}, format="json",
            **admin_auth_headers,
        )

        # Assert
        assert respuesta.status_code == 200
        data = respuesta.json()["data"]
        assert data["activo"] is False
        assert data["credenciales_desactivadas"] == 2
        assert data["motivo_suspension"] == "contrato vencido"

    def test_sin_motivo_returns_400(
        self, api_client, partner_con_credenciales, admin_auth_headers
    ):
        """CA-PAC-011 — escenario L."""
        assert api_client.post(
            SUSPENDER, {"motivo": ""}, format="json", **admin_auth_headers
        ).status_code == 400

    def test_un_partner_no_puede_suspender_returns_403(
        self, api_client, partner_con_credenciales, partner_auth_headers
    ):
        """Suspender es control excepcional del Administrador, no autoservicio
        (a diferencia de revocar, que sí lo es)."""
        # Act
        respuesta = api_client.post(
            SUSPENDER, {"motivo": "prueba"}, format="json", **partner_auth_headers
        )

        # Assert
        assert respuesta.status_code == 403
        assert next(
            p for p in PINOT_STORE["Dim_Partner"] if p["idpartner"] == 1
        )["activo"] is True

    def test_suspender_uno_ya_suspendido_returns_409(
        self, api_client, partner_suspendido, admin_auth_headers
    ):
        assert api_client.post(
            SUSPENDER, {"motivo": "otra vez"}, format="json", **admin_auth_headers
        ).status_code == 409

    def test_partner_inexistente_returns_404(
        self, api_client, partner_con_credenciales, admin_auth_headers
    ):
        assert api_client.post(
            "/api/v1/partners/9999/suspender", {"motivo": "x"}, format="json",
            **admin_auth_headers,
        ).status_code == 404


class TestReactivar:
    def test_reactiva_y_desglosa_restituidas_y_no_restituidas(
        self, api_client, partner_suspendido, admin_auth_headers
    ):
        """El desglose hace VISIBLE que no todas vuelven: si el Administrador
        esperaba tres y ve dos, la respuesta ya le explicó por qué."""
        # Act
        respuesta = api_client.post(
            REACTIVAR, {"motivo": "deuda regularizada"}, format="json",
            **admin_auth_headers,
        )

        # Assert
        assert respuesta.status_code == 200
        data = respuesta.json()["data"]
        assert data["activo"] is True
        assert data["credenciales_restituidas"] == 2
        assert data["credenciales_no_restituidas"] == 1

    def test_el_motivo_es_opcional_al_reactivar(
        self, api_client, partner_suspendido, admin_auth_headers
    ):
        """El SRS exige motivo al cortar el acceso, no al devolverlo."""
        assert api_client.post(
            REACTIVAR, {}, format="json", **admin_auth_headers
        ).status_code == 200

    def test_reactivar_un_partner_no_suspendido_returns_409(
        self, api_client, partner_con_credenciales, admin_auth_headers
    ):
        """CA-PAC-011 — escenario K, sin entrada en la bitácora."""
        # Arrange
        antes = len(PINOT_STORE["Fact_HistorialAccesoPartner"])

        # Act
        respuesta = api_client.post(REACTIVAR, {}, format="json", **admin_auth_headers)

        # Assert
        assert respuesta.status_code == 409
        assert len(PINOT_STORE["Fact_HistorialAccesoPartner"]) == antes

    def test_un_partner_no_puede_reactivarse_a_si_mismo(
        self, api_client, partner_suspendido, partner_auth_headers
    ):
        """RN-PAC-009 — reabrir un acceso cortado es siempre decisión de un
        Administrador. Si el propio suspendido pudiera, la suspensión no
        significaría nada."""
        # Act
        respuesta = api_client.post(REACTIVAR, {}, format="json", **partner_auth_headers)

        # Assert
        assert respuesta.status_code == 403
        assert next(
            p for p in PINOT_STORE["Dim_Partner"] if p["idpartner"] == 1
        )["activo"] is False

    def test_sin_autenticacion_returns_401(self, api_client, partner_suspendido):
        assert api_client.post(REACTIVAR, {}, format="json").status_code == 401
