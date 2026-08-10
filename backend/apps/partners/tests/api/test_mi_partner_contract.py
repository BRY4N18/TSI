"""BE-DELTA-01 — `GET /api/v1/partners/me` (FR-UI-013).

Sin este endpoint el portal del partner es INALCANZABLE: el token de sesion
solo lleva `idusuario`, todos los demas endpoints exigen `{idpartner}` en la
ruta y `GET /partners` es de gestores. El partner no tiene forma de averiguar
su propio id.

Detectado al especificar el frontend, no al implementar el backend: es el tipo
de hueco que solo se ve desde la interfaz.
"""

from __future__ import annotations

import json

import pytest

from conftest import PINOT_STORE

pytestmark = [pytest.mark.django_db, pytest.mark.api]

# `partner_auth_headers` vincula el usuario 51 al cliente 1.
ID_CLIENTE_DEL_PARTNER = 1
ID_PARTNER = 980
URL = "/api/v1/partners/me"


@pytest.fixture
def partner_del_usuario(mock_pinot, mock_kafka):
    PINOT_STORE["Dim_Partner"].append(
        {
            "idpartner": ID_PARTNER,
            "idcliente": ID_CLIENTE_DEL_PARTNER,
            "nombrepartner": "Aseguradora del usuario 51",
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


class TestResolucionDelPartnerPropio:
    def test_me_when_partner_existe_returns_200(
        self, api_client, partner_del_usuario, partner_auth_headers
    ):
        # Act
        response = api_client.get(URL, **partner_auth_headers)

        # Assert
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["idpartner"] == ID_PARTNER
        assert data["idcliente"] == ID_CLIENTE_DEL_PARTNER

    def test_me_devuelve_el_detalle_completo_con_estado_derivado(
        self, api_client, partner_del_usuario, partner_auth_headers
    ):
        """El portal necesita estado, credenciales e historial en una llamada."""
        # Act
        data = api_client.get(URL, **partner_auth_headers).json()["data"]

        # Assert
        assert data["estado"] == "Plan asignado"
        assert "credenciales" in data
        assert "historial" in data

    def test_me_no_expone_el_hash_del_secreto(
        self, api_client, partner_del_usuario, partner_auth_headers
    ):
        """RN-PON-005 — ninguna consulta expone material del secreto."""
        # Arrange
        PINOT_STORE["Dim_CredencialAPI"].append(
            {
                "idcredencial": 9801,
                "idpartner": ID_PARTNER,
                "idcliente": ID_CLIENTE_DEL_PARTNER,
                "client_secret_hash": "$2b$12$hash-que-no-debe-salir",
                "nombre_credencial": "pruebas",
                "entorno": "Sandbox",
                "activo": True,
                "fecha_creacion": 1,
                "fecha_expiracion": 253402300799000,
                "fecha_actualizacion": 1,
            }
        )

        # Act
        cuerpo = api_client.get(URL, **partner_auth_headers).json()["data"]

        # Assert
        assert "hash-que-no-debe-salir" not in json.dumps(cuerpo)
        assert "client_secret" not in json.dumps(cuerpo)


class TestAusencias:
    def test_me_when_usuario_sin_partner_returns_404(
        self, api_client, mock_pinot, mock_kafka, partner_auth_headers
    ):
        """El 404 se presenta como explicación, no como pantalla rota."""
        # Act — el cliente existe pero no tiene perfil de partner
        response = api_client.get(URL, **partner_auth_headers)

        # Assert
        assert response.status_code == 404
        assert response.json()["code"] in ("sin_partner", "sin_cliente")

    def test_me_when_sin_token_returns_401(self, api_client, partner_del_usuario):
        # Act / Assert
        assert api_client.get(URL).status_code == 401


class TestAislamientoEntrePartners:
    def test_me_nunca_devuelve_el_partner_de_otro_cliente(
        self, api_client, partner_del_usuario, partner_ajeno_auth_headers
    ):
        """Por construcción solo puede devolver el propio: resuelve desde el
        cliente del usuario, no desde un id que llegue por la petición."""
        # Act — usuario de otro cliente, sin partner propio
        response = api_client.get(URL, **partner_ajeno_auth_headers)

        # Assert
        assert response.status_code == 404
        assert str(ID_PARTNER) not in response.content.decode()


class TestAccesoDeGestores:
    def test_me_when_gestor_sin_partner_returns_404_y_no_rompe(
        self, api_client, partner_del_usuario, devapis_auth_headers
    ):
        """Un gestor puede llamarlo; simplemente no tiene partner propio."""
        # Act
        response = api_client.get(URL, **devapis_auth_headers)

        # Assert
        assert response.status_code in (200, 404)
