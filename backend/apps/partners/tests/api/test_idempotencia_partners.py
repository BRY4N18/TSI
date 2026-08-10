"""Idempotency-Key en los cinco endpoints de escritura (api-standards).

El caso que de verdad importa esta en `TestEmisionDeCredencial`: sin
idempotencia, un reintento por timeout emite una credencial de mas Y pierde
el secreto de la primera para siempre, porque de aquella solo se persistio el
hash (RN-PON-005). Es el unico endpoint del modulo donde un reintento no
idempotente destruye informacion irrecuperable.
"""

from __future__ import annotations

import json

import pytest

from conftest import PINOT_STORE

pytestmark = [pytest.mark.django_db, pytest.mark.api]

ID_CLIENTE_DEL_PARTNER = 1
ID_PARTNER = 960

LIMITES = json.dumps(
    {"unidades_max": 25, "usuarios_max": 10, "api_calls_mes": 10000, "api_calls_minuto": 120}
)


@pytest.fixture
def partner_con_plan(mock_pinot, mock_kafka):
    PINOT_STORE["Dim_Partner"].append(
        {
            "idpartner": ID_PARTNER,
            "idcliente": ID_CLIENTE_DEL_PARTNER,
            "nombrepartner": "Demo Idempotencia",
            "contacto_tecnico_nombre": "Ana",
            "contacto_tecnico_gmail": "ana@demo.com",
            "planapi": "Profesional",
            "limitellamadasmes": 10000,
            "limitellamadasminuto": 120,
            "sandbox_activado": 0,
            "sandbox_expiracion": 0,
            "fecha_suspension": "",
            "motivo_suspension": "",
            "activo": True,
            "fecha_actualizacion": 1,
        }
    )
    return ID_PARTNER


@pytest.fixture
def cliente_integrador(mock_pinot, mock_kafka):
    PINOT_STORE["Dim_Cliente"].append({"idcliente": 961, "nombre": "Aseguradora"})
    PINOT_STORE["Dim_Plan"].append(
        {"idplan": 961, "nombre": "Profesional", "limites": LIMITES, "activo": True}
    )
    PINOT_STORE["Fact_Suscripcion"].append(
        {
            "id_suscripcion": 961,
            "idcliente": 961,
            "idplan": 961,
            "estado": "Activa",
            "activo": True,
            "fecha_inicio": 1,
        }
    )
    return 961


def _con_clave(headers, clave):
    return {**headers, "HTTP_IDEMPOTENCY_KEY": clave}


class TestEmisionDeCredencial:
    """El endpoint donde la idempotencia protege algo irrecuperable."""

    def test_reintento_con_la_misma_clave_devuelve_el_mismo_secreto(
        self, api_client, partner_con_plan, partner_auth_headers
    ):
        # Arrange
        cabeceras = _con_clave(partner_auth_headers, "clave-reintento-1")
        cuerpo = {"nombre_credencial": "siniestros", "entorno": "Sandbox"}

        # Act — el cliente reintenta tras perder la primera respuesta
        primera = api_client.post(
            f"/api/v1/partners/{ID_PARTNER}/credenciales", cuerpo, format="json", **cabeceras
        )
        segunda = api_client.post(
            f"/api/v1/partners/{ID_PARTNER}/credenciales", cuerpo, format="json", **cabeceras
        )

        # Assert — mismo secreto: el reintento lo RECUPERA en vez de perderlo
        assert primera.status_code == 201
        assert segunda.status_code == 201
        assert segunda.json()["data"]["client_secret"] == primera.json()["data"]["client_secret"]

    def test_reintento_con_la_misma_clave_no_emite_una_segunda_credencial(
        self, api_client, partner_con_plan, partner_auth_headers
    ):
        # Arrange
        cabeceras = _con_clave(partner_auth_headers, "clave-reintento-2")
        cuerpo = {"nombre_credencial": "siniestros", "entorno": "Sandbox"}

        # Act
        api_client.post(
            f"/api/v1/partners/{ID_PARTNER}/credenciales", cuerpo, format="json", **cabeceras
        )
        api_client.post(
            f"/api/v1/partners/{ID_PARTNER}/credenciales", cuerpo, format="json", **cabeceras
        )

        # Assert
        credenciales = [
            c for c in PINOT_STORE["Dim_CredencialAPI"] if c["idpartner"] == ID_PARTNER
        ]
        assert len(credenciales) == 1

    def test_claves_distintas_emiten_credenciales_distintas(
        self, api_client, partner_con_plan, partner_auth_headers
    ):
        """Dos intenciones distintas no deben colapsar en una."""
        # Act
        primera = api_client.post(
            f"/api/v1/partners/{ID_PARTNER}/credenciales",
            {"nombre_credencial": "sistema-a", "entorno": "Sandbox"},
            format="json",
            **_con_clave(partner_auth_headers, "clave-a"),
        )
        segunda = api_client.post(
            f"/api/v1/partners/{ID_PARTNER}/credenciales",
            {"nombre_credencial": "sistema-b", "entorno": "Sandbox"},
            format="json",
            **_con_clave(partner_auth_headers, "clave-b"),
        )

        # Assert
        assert primera.json()["data"]["idcredencial"] != segunda.json()["data"]["idcredencial"]

    def test_sin_clave_el_endpoint_sigue_funcionando(
        self, api_client, partner_con_plan, partner_auth_headers
    ):
        """La cabecera es opcional: su ausencia no puede romper el endpoint."""
        # Act
        response = api_client.post(
            f"/api/v1/partners/{ID_PARTNER}/credenciales",
            {"nombre_credencial": "sin-clave", "entorno": "Sandbox"},
            format="json",
            **partner_auth_headers,
        )

        # Assert
        assert response.status_code == 201


class TestRegistroDePartner:
    def test_reintento_devuelve_la_misma_respuesta_y_no_duplica(
        self, api_client, cliente_integrador, devapis_auth_headers
    ):
        # Arrange
        cabeceras = _con_clave(devapis_auth_headers, "clave-registro")
        cuerpo = {
            "idcliente": 961,
            "nombrepartner": "Aseguradora Demo",
            "contacto_tecnico_nombre": "Ana",
            "contacto_tecnico_gmail": "ana@demo.com",
        }

        # Act
        primera = api_client.post("/api/v1/partners", cuerpo, format="json", **cabeceras)
        segunda = api_client.post("/api/v1/partners", cuerpo, format="json", **cabeceras)

        # Assert — sin idempotencia la segunda seria un 409 por RN-PON-002
        assert primera.status_code == 201
        assert segunda.status_code == 201
        assert segunda.json()["data"]["idpartner"] == primera.json()["data"]["idpartner"]


class TestAsignacionDePlan:
    def test_reintento_devuelve_la_misma_respuesta(
        self, api_client, partner_con_plan, devapis_auth_headers
    ):
        # Arrange
        cabeceras = _con_clave(devapis_auth_headers, "clave-plan")

        # Act
        primera = api_client.post(
            f"/api/v1/partners/{ID_PARTNER}/plan-acceso", {}, format="json", **cabeceras
        )
        segunda = api_client.post(
            f"/api/v1/partners/{ID_PARTNER}/plan-acceso", {}, format="json", **cabeceras
        )

        # Assert
        assert primera.status_code == segunda.status_code
        assert segunda.json()["data"] == primera.json()["data"]


class TestNoSeCacheanLosErrores:
    def test_un_409_no_queda_cacheado(
        self, api_client, mock_pinot, mock_kafka, partner_auth_headers
    ):
        """Si el conflicto se resuelve, el mismo reintento debe poder triunfar.

        Aqui la emision falla por «sin plan»; tras asignarlo, la MISMA clave
        debe emitir de verdad y no devolver el 409 congelado.
        """
        # Arrange — partner SIN plan
        PINOT_STORE["Dim_Partner"].append(
            {
                "idpartner": ID_PARTNER,
                "idcliente": ID_CLIENTE_DEL_PARTNER,
                "nombrepartner": "Sin plan",
                "contacto_tecnico_nombre": "Ana",
                "contacto_tecnico_gmail": "ana@demo.com",
                "planapi": "",
                "limitellamadasmes": -1,
                "limitellamadasminuto": -1,
                "sandbox_activado": 0,
                "sandbox_expiracion": 0,
                "fecha_suspension": "",
                "motivo_suspension": "",
                "activo": True,
                "fecha_actualizacion": 1,
            }
        )
        cabeceras = _con_clave(partner_auth_headers, "clave-conflicto")
        cuerpo = {"nombre_credencial": "siniestros", "entorno": "Sandbox"}

        # Act
        fallida = api_client.post(
            f"/api/v1/partners/{ID_PARTNER}/credenciales", cuerpo, format="json", **cabeceras
        )
        # El plan llega despues
        for p in PINOT_STORE["Dim_Partner"]:
            if p["idpartner"] == ID_PARTNER:
                p["planapi"] = "Profesional"
        reintento = api_client.post(
            f"/api/v1/partners/{ID_PARTNER}/credenciales", cuerpo, format="json", **cabeceras
        )

        # Assert
        assert fallida.status_code == 409
        assert reintento.status_code == 201
