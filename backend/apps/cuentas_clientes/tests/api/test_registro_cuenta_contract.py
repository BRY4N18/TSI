import pytest


@pytest.mark.api
class TestRegistroCuentaContract:
    def test_registrar_when_admin_returns_201(self, api_client, auth_headers):
        # Arrange
        payload = {
            "razon_social": "Nueva Aseguradora S.A.",
            "nombre": "Nueva Aseguradora",
            "tipo": "Aseguradora",
            "nit_identificacion": "700123456-9",
            "fecha_inicio_contrato": 1704067200000,
            "admin_local": {
                "nombres": "Pedro",
                "apellidos": "Nuevo",
                "gmail": "nuevo.admin@tsi.com",
            },
        }

        # Act
        response = api_client.post(
            "/api/v1/cuentas-clientes",
            payload,
            format="json",
            **auth_headers,
        )

        # Assert
        assert response.status_code == 201
        body = response.json()
        assert body["data"]["estado"] == "Activo"
        assert "idcliente" in body["data"]
        assert "admin_local_id" in body["data"]

    def test_registrar_when_duplicate_nit_returns_409(self, api_client, auth_headers):
        # Arrange
        payload = {
            "razon_social": "Duplicado",
            "nombre": "Dup",
            "tipo": "Municipio",
            "nit_identificacion": "900123456-1",
            "fecha_inicio_contrato": 1704067200000,
            "admin_local": {
                "nombres": "A",
                "apellidos": "B",
                "gmail": "dup@tsi.com",
            },
        }

        # Act
        response = api_client.post(
            "/api/v1/cuentas-clientes",
            payload,
            format="json",
            **auth_headers,
        )

        # Assert
        assert response.status_code == 409

    def test_registrar_when_unauthenticated_returns_401(self, api_client):
        # Act
        response = api_client.post("/api/v1/cuentas-clientes", {}, format="json")

        # Assert
        assert response.status_code == 401
