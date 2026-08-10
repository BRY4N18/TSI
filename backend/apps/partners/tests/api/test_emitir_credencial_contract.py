"""Contrato de `POST/GET /api/v1/partners/{id}/credenciales` (CU-O49)."""

from __future__ import annotations

import json

import pytest

from conftest import PINOT_STORE

pytestmark = [pytest.mark.django_db, pytest.mark.api]

# El fixture `partner_auth_headers` vincula el usuario 51 al cliente 1.
ID_CLIENTE_DEL_PARTNER = 1
ID_PARTNER = 904


@pytest.fixture
def partner_con_plan(mock_pinot, mock_kafka):
    PINOT_STORE["Dim_Partner"].append(
        {
            "idpartner": ID_PARTNER,
            "idcliente": ID_CLIENTE_DEL_PARTNER,
            "nombrepartner": "Demo",
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


class TestEmitirCredencialContract:
    def test_emitir_when_partner_propio_returns_201_con_secreto(
        self, api_client, partner_con_plan, partner_auth_headers
    ):
        # Act
        response = api_client.post(
            f"/api/v1/partners/{ID_PARTNER}/credenciales",
            {"nombre_credencial": "plataforma-siniestros", "entorno": "Sandbox"},
            format="json",
            **partner_auth_headers,
        )

        # Assert
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["client_secret"]
        assert data["client_id"]
        assert "client_secret_hash" not in data

    def test_emitir_when_partner_ajeno_returns_403(
        self, api_client, partner_con_plan, partner_ajeno_auth_headers
    ):
        """Control de propiedad: nadie emite credenciales en perfil ajeno."""
        # Act
        response = api_client.post(
            f"/api/v1/partners/{ID_PARTNER}/credenciales",
            {"nombre_credencial": "intruso"},
            format="json",
            **partner_ajeno_auth_headers,
        )

        # Assert
        assert response.status_code == 403
        assert PINOT_STORE["Dim_CredencialAPI"] == []

    def test_emitir_when_entorno_produccion_returns_403(
        self, api_client, partner_con_plan, partner_auth_headers
    ):
        """Produccion exige solicitud + aprobacion, no autoservicio (RF-PON-008)."""
        # Act
        response = api_client.post(
            f"/api/v1/partners/{ID_PARTNER}/credenciales",
            {"nombre_credencial": "prod", "entorno": "Producción"},
            format="json",
            **partner_auth_headers,
        )

        # Assert
        assert response.status_code == 403
        assert response.json()["code"] == "produccion_requiere_aprobacion"

    def test_emitir_when_sin_plan_returns_409(
        self, api_client, mock_pinot, mock_kafka, partner_auth_headers
    ):
        # Arrange — partner sin plan (centinela cadena vacia)
        PINOT_STORE["Dim_Partner"].append(
            {
                "idpartner": 905,
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

        # Act
        response = api_client.post(
            "/api/v1/partners/905/credenciales",
            {"nombre_credencial": "x"},
            format="json",
            **partner_auth_headers,
        )

        # Assert
        assert response.status_code == 409
        assert response.json()["code"] == "sin_plan"

    def test_emitir_when_nombre_vacio_returns_400(
        self, api_client, partner_con_plan, partner_auth_headers
    ):
        # Act
        response = api_client.post(
            f"/api/v1/partners/{ID_PARTNER}/credenciales",
            {"nombre_credencial": ""},
            format="json",
            **partner_auth_headers,
        )

        # Assert
        assert response.status_code == 400

    def test_emitir_when_sin_token_returns_401(self, api_client, partner_con_plan):
        # Act
        response = api_client.post(
            f"/api/v1/partners/{ID_PARTNER}/credenciales",
            {"nombre_credencial": "x"},
            format="json",
        )

        # Assert
        assert response.status_code == 401


class TestListarCredencialesContract:
    def test_listar_when_propio_returns_200_sin_secretos(
        self, api_client, partner_con_plan, partner_auth_headers
    ):
        """RN-PON-005 — ningun GET devuelve el secreto ni su hash."""
        # Arrange
        creada = api_client.post(
            f"/api/v1/partners/{ID_PARTNER}/credenciales",
            {"nombre_credencial": "sistema-a"},
            format="json",
            **partner_auth_headers,
        ).json()["data"]

        # Act
        response = api_client.get(
            f"/api/v1/partners/{ID_PARTNER}/credenciales", **partner_auth_headers
        )

        # Assert
        assert response.status_code == 200
        cuerpo = json.dumps(response.json())
        assert "client_secret_hash" not in cuerpo
        assert creada["client_secret"] not in cuerpo

    def test_listar_when_ajeno_returns_403(
        self, api_client, partner_con_plan, partner_ajeno_auth_headers
    ):
        # Act
        response = api_client.get(
            f"/api/v1/partners/{ID_PARTNER}/credenciales", **partner_ajeno_auth_headers
        )

        # Assert
        assert response.status_code == 403
