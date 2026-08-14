"""Rechazos de acceso a la API de datos (RF-APM-001, D2 de #09).

La afirmación que sostiene todo el archivo es negativa: **ningún rechazo puede
dejar fila en `Fact_APIIntegracion`**. Si la dejara, se estaría facturando una
llamada que nunca se atendió.

El acceso exige tres condiciones con tres dueños distintos, y cada una tiene su
código: credencial inválida → **401**; partner suspendido o cliente sin
suscripción vigente → **403**.
"""

from __future__ import annotations

import pytest

from conftest import PINOT_STORE

pytestmark = [pytest.mark.django_db, pytest.mark.api]

URL = "/api/v1/datos/accidentes"
ID_PARTNER = 880


def _suscripcion_vigente(idcliente=ID_PARTNER, estado="Activa"):
    PINOT_STORE["Dim_Plan"].append({
        "idplan": idcliente,
        "nombre": "Profesional",
        "limites": '{"api_calls_mes": 10000, "api_calls_minuto": 120}',
        "severidades_desbloqueadas": "null",
        "activo": True,
    })
    PINOT_STORE["Fact_Suscripcion"].append({
        "id_suscripcion": idcliente,
        "idcliente": idcliente,
        "idplan": idcliente,
        "estado": estado,
        "activo": True,
        "fecha_inicio": 1,
        "severidades_desbloqueadas": "[1, 2]",
    })


def _sin_consumo_registrado():
    return PINOT_STORE["Fact_APIIntegracion"] == []


class TestCredencialInvalida:
    def test_sin_cabeceras_returns_401(self, api_client, mock_pinot, mock_kafka):
        # Act
        response = api_client.get(URL)

        # Assert
        assert response.status_code == 401
        assert _sin_consumo_registrado()

    def test_un_jwt_humano_no_abre_la_api_de_datos(
        self, api_client, devapis_auth_headers
    ):
        """Dos poblaciones distintas: el JWT vale para las pantallas, no aquí."""
        # Act
        response = api_client.get(URL, **devapis_auth_headers)

        # Assert
        assert response.status_code == 401
        assert _sin_consumo_registrado()

    def test_secreto_incorrecto_returns_401(
        self, api_client, credencial_produccion_headers
    ):
        # Arrange
        _suscripcion_vigente()
        cabeceras = {**credencial_produccion_headers, "HTTP_X_CLIENT_SECRET": "no-es"}

        # Act
        response = api_client.get(URL, **cabeceras)

        # Assert
        assert response.status_code == 401
        assert _sin_consumo_registrado()

    def test_credencial_revocada_returns_401(
        self, api_client, credencial_produccion_headers
    ):
        # Arrange
        _suscripcion_vigente()
        for c in PINOT_STORE["Dim_CredencialAPI"]:
            c["activo"] = False

        # Act
        response = api_client.get(URL, **credencial_produccion_headers)

        # Assert
        assert response.status_code == 401
        assert _sin_consumo_registrado()

    def test_credencial_vencida_returns_401(
        self, api_client, credencial_produccion_headers
    ):
        """La vigencia se deriva del dato, no de que un job la haya marcado."""
        # Arrange
        _suscripcion_vigente()
        for c in PINOT_STORE["Dim_CredencialAPI"]:
            c["fecha_expiracion"] = 1000

        # Act
        response = api_client.get(URL, **credencial_produccion_headers)

        # Assert
        assert response.status_code == 401
        assert _sin_consumo_registrado()


class TestPartnerOSuscripcionSuspendidos:
    def test_partner_suspendido_returns_403(
        self, api_client, credencial_produccion_headers
    ):
        """403 y no 401: sabemos quién es; lo que falla es su derecho."""
        # Arrange
        _suscripcion_vigente()
        for p in PINOT_STORE["Dim_Partner"]:
            p["activo"] = False

        # Act
        response = api_client.get(URL, **credencial_produccion_headers)

        # Assert
        assert response.status_code == 403
        assert _sin_consumo_registrado()

    def test_cliente_sin_suscripcion_vigente_returns_403(
        self, api_client, credencial_produccion_headers
    ):
        """El hueco que cerró D2: la credencial y el partner están perfectos,
        pero el cliente dejó de pagar."""
        # Arrange
        _suscripcion_vigente(estado="Cancelada")

        # Act
        response = api_client.get(URL, **credencial_produccion_headers)

        # Assert
        assert response.status_code == 403
        assert _sin_consumo_registrado()

    def test_cliente_sin_ninguna_suscripcion_returns_403(
        self, api_client, credencial_produccion_headers
    ):
        # Act — no se sembró suscripción alguna
        response = api_client.get(URL, **credencial_produccion_headers)

        # Assert
        assert response.status_code == 403
        assert _sin_consumo_registrado()


class TestNingunRechazoSeFactura:
    def test_ningun_rechazo_deja_consumo_facturable(
        self, api_client, credencial_produccion_headers
    ):
        """Recorre los rechazos de golpe: facturar una llamada no atendida
        sería cobrar por un servicio que no se prestó."""
        # Arrange
        _suscripcion_vigente(estado="Cancelada")

        # Act
        api_client.get(URL)
        api_client.get(URL, **credencial_produccion_headers)
        api_client.get(URL, HTTP_X_CLIENT_ID="tsi-p1-c1", HTTP_X_CLIENT_SECRET="x")

        # Assert
        assert _sin_consumo_registrado()
