import pytest


@pytest.mark.api
class TestUsersContract:
    def test_list_users_when_admin_returns_envelope(self, api_client, auth_headers):
        # Arrange / Act
        response = api_client.get("/api/v1/usuarios", **auth_headers)

        # Assert
        assert response.status_code == 200
        body = response.json()
        assert "data" in body
        assert isinstance(body["data"], list)

    def test_create_user_when_admin_returns_user(self, api_client, auth_headers):
        # Arrange
        payload = {
            "nombres": "API",
            "apellidos": "Test",
            "gmail": "apitest@tsi.com",
            "password": "password123",
            "role_ids": [2],
        }

        # Act
        response = api_client.post("/api/v1/usuarios", payload, format="json", **auth_headers)

        # Assert
        assert response.status_code == 200
        assert response.json()["data"]["gmail"] == "apitest@tsi.com"

    def test_list_users_when_not_admin_returns_403(self, api_client, operator_auth_headers):
        # Arrange / Act
        response = api_client.get("/api/v1/usuarios", **operator_auth_headers)

        # Assert
        assert response.status_code == 403
