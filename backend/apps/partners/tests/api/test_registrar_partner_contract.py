"""Contrato de `POST /api/v1/partners` y consulta (CU-O48, RF-PON-012)."""

from __future__ import annotations

import json

import pytest

from conftest import PINOT_STORE

pytestmark = [pytest.mark.django_db, pytest.mark.api]

LIMITES = json.dumps(
    {"unidades_max": 25, "usuarios_max": 10, "api_calls_mes": 10000, "api_calls_minuto": 120}
)


@pytest.fixture
def cliente_integrador(mock_pinot, mock_kafka):
    """Cliente 902 con suscripcion vigente sobre el plan 902."""
    PINOT_STORE["Dim_Cliente"].append({"idcliente": 902, "nombre": "Aseguradora"})
    PINOT_STORE["Dim_Plan"].append(
        {"idplan": 902, "nombre": "Profesional", "limites": LIMITES, "activo": True}
    )
    PINOT_STORE["Fact_Suscripcion"].append(
        {
            "id_suscripcion": 902,
            "idcliente": 902,
            "idplan": 902,
            "estado": "Activa",
            "activo": True,
            "fecha_inicio": 1,
        }
    )
    return 902


PAYLOAD = {
    "idcliente": 902,
    "nombrepartner": "Aseguradora Demo",
    "contacto_tecnico_nombre": "Ana Torres",
    "contacto_tecnico_gmail": "ana@aseguradora.com",
}


class TestRegistrarPartnerContract:
    def test_registrar_when_valido_returns_201(
        self, api_client, cliente_integrador, devapis_auth_headers
    ):
        # Act
        response = api_client.post(
            "/api/v1/partners", PAYLOAD, format="json", **devapis_auth_headers
        )

        # Assert
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["estado"] == "Registrado"
        assert data["planapi"] == ""  # centinela, no None ni 'null'
        assert data["limitellamadasmes"] == -1

    def test_registrar_when_cliente_inexistente_returns_404(
        self, api_client, mock_pinot, mock_kafka, devapis_auth_headers
    ):
        # Act
        response = api_client.post(
            "/api/v1/partners",
            {**PAYLOAD, "idcliente": 99999},
            format="json",
            **devapis_auth_headers,
        )

        # Assert
        assert response.status_code == 404

    def test_registrar_when_duplicado_returns_409_con_idpartner_existente(
        self, api_client, cliente_integrador, devapis_auth_headers
    ):
        """RN-PON-002 — la respuesta indica cual es el partner existente."""
        # Arrange
        primero = api_client.post(
            "/api/v1/partners", PAYLOAD, format="json", **devapis_auth_headers
        )
        assert primero.status_code == 201

        # Act
        segundo = api_client.post(
            "/api/v1/partners", PAYLOAD, format="json", **devapis_auth_headers
        )

        # Assert
        assert segundo.status_code == 409
        cuerpo = segundo.json()
        assert cuerpo["code"] == "partner_duplicado"
        assert cuerpo["idpartner_existente"] == primero.json()["data"]["idpartner"]

    def test_registrar_when_falta_campo_returns_400(
        self, api_client, cliente_integrador, devapis_auth_headers
    ):
        # Act
        response = api_client.post(
            "/api/v1/partners",
            {"idcliente": 902, "nombrepartner": "Solo nombre"},
            format="json",
            **devapis_auth_headers,
        )

        # Assert
        assert response.status_code == 400

    def test_registrar_when_sin_token_returns_401(self, api_client, cliente_integrador):
        # Act
        response = api_client.post("/api/v1/partners", PAYLOAD, format="json")

        # Assert
        assert response.status_code == 401

    def test_registrar_when_rol_partner_returns_403(
        self, api_client, cliente_integrador, partner_auth_headers
    ):
        """El registro lo hace un gestor, no el propio partner."""
        # Act
        response = api_client.post(
            "/api/v1/partners", PAYLOAD, format="json", **partner_auth_headers
        )

        # Assert
        assert response.status_code == 403


class TestConsultaPartnerContract:
    def test_detalle_when_existe_returns_200_sin_secreto(
        self, api_client, cliente_integrador, devapis_auth_headers
    ):
        """RN-PON-005 — ninguna consulta expone el secreto ni su hash."""
        # Arrange
        creado = api_client.post(
            "/api/v1/partners", PAYLOAD, format="json", **devapis_auth_headers
        ).json()["data"]
        PINOT_STORE["Dim_CredencialAPI"].append(
            {
                "idcredencial": 9001,
                "idpartner": creado["idpartner"],
                "idcliente": 902,
                "client_secret_hash": "$2b$12$hash-que-no-debe-salir",
                "nombre_credencial": "sistema-siniestros",
                "entorno": "Sandbox",
                "activo": True,
                "fecha_creacion": 1,
                "fecha_expiracion": 253402300799000,
                "fecha_actualizacion": 1,
            }
        )

        # Act
        response = api_client.get(
            f"/api/v1/partners/{creado['idpartner']}", **devapis_auth_headers
        )

        # Assert
        assert response.status_code == 200
        cuerpo = response.json()["data"]
        assert cuerpo["credenciales"][0]["nombre_credencial"] == "sistema-siniestros"
        assert "client_secret_hash" not in cuerpo["credenciales"][0]
        assert "client_secret" not in cuerpo["credenciales"][0]
        # Y el hash no aparece en ninguna parte del cuerpo serializado
        assert "hash-que-no-debe-salir" not in json.dumps(cuerpo)

    def test_detalle_when_partner_ajeno_returns_403(
        self, api_client, cliente_integrador, devapis_auth_headers, partner_ajeno_auth_headers
    ):
        """Control de propiedad: un partner no ve el perfil de otro."""
        # Arrange
        creado = api_client.post(
            "/api/v1/partners", PAYLOAD, format="json", **devapis_auth_headers
        ).json()["data"]

        # Act — el partner del cliente 999 intenta ver el del cliente 902
        response = api_client.get(
            f"/api/v1/partners/{creado['idpartner']}", **partner_ajeno_auth_headers
        )

        # Assert
        assert response.status_code == 403

    def test_listar_when_hay_partners_returns_200_con_paginacion(
        self, api_client, cliente_integrador, devapis_auth_headers
    ):
        # Arrange
        api_client.post("/api/v1/partners", PAYLOAD, format="json", **devapis_auth_headers)

        # Act
        response = api_client.get("/api/v1/partners", **devapis_auth_headers)

        # Assert
        assert response.status_code == 200
        cuerpo = response.json()
        assert len(cuerpo["data"]) >= 1
        assert "pagination" in cuerpo["meta"]


class TestAsignarPlanContract:
    def test_asignar_plan_when_valido_returns_200_con_cupo(
        self, api_client, cliente_integrador, devapis_auth_headers
    ):
        # Arrange
        creado = api_client.post(
            "/api/v1/partners", PAYLOAD, format="json", **devapis_auth_headers
        ).json()["data"]

        # Act
        response = api_client.post(
            f"/api/v1/partners/{creado['idpartner']}/plan-acceso",
            {},
            format="json",
            **devapis_auth_headers,
        )

        # Assert — el cupo viene del plan contratado
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["estado"] == "Plan asignado"
        assert data["limitellamadasmes"] == 10000
        assert data["limitellamadasminuto"] == 120

    def test_asignar_plan_when_partner_inexistente_returns_404(
        self, api_client, mock_pinot, mock_kafka, devapis_auth_headers
    ):
        # Act
        response = api_client.post(
            "/api/v1/partners/404404/plan-acceso", {}, format="json", **devapis_auth_headers
        )

        # Assert
        assert response.status_code == 404
