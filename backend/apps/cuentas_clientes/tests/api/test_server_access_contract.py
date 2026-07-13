import pytest


@pytest.mark.api
class TestServerAccessContract:
    def test_list_server_users_when_admin_returns_envelope(self, api_client, auth_headers):
        # Arrange / Act
        response = api_client.get("/api/v1/server-access/usuarios", **auth_headers)

        # Assert
        assert response.status_code == 200
        assert "data" in response.json()

    def test_create_server_user_when_admin_succeeds(self, api_client, auth_headers):
        # Arrange
        payload = {"usuario": "kafka-admin", "contrasena": "secure123"}

        # Act
        response = api_client.post(
            "/api/v1/server-access/usuarios", payload, format="json", **auth_headers
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["data"]["usuario"] == "kafka-admin"

    def test_create_server_role_when_admin_succeeds(self, api_client, auth_headers):
        # Arrange
        payload = {"rolservidor": "pinot-reader", "descripcion": "Read-only Pinot"}

        # Act
        response = api_client.post(
            "/api/v1/server-access/roles", payload, format="json", **auth_headers
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["data"]["rolservidor"] == "pinot-reader"

    def test_server_access_when_operador_returns_403(self, api_client, operator_auth_headers):
        # Arrange / Act
        response = api_client.get("/api/v1/server-access/usuarios", **operator_auth_headers)

        # Assert
        assert response.status_code == 403
