import pytest


@pytest.mark.api
class TestAuthLoginContract:
    def test_login_when_valid_credentials_returns_envelope(self, api_client):
        # Arrange
        payload = {"gmail": "admin@tsi.com", "password": "password123"}

        # Act
        response = api_client.post("/api/v1/auth/login", payload, format="json")

        # Assert
        assert response.status_code == 200
        body = response.json()
        assert "data" in body
        assert "meta" in body
        assert "accessToken" in body["data"]
        assert "refreshToken" in body["data"]
        assert body["data"]["tokenType"] == "Bearer"
        assert body["data"]["expiresInSeconds"] == 3600
        assert body["data"]["profile"]["gmail"] == "admin@tsi.com"

    def test_login_when_invalid_credentials_returns_401(self, api_client):
        # Arrange
        payload = {"gmail": "admin@tsi.com", "password": "wrongpassword"}

        # Act
        response = api_client.post("/api/v1/auth/login", payload, format="json")

        # Assert
        assert response.status_code == 401
        body = response.json()
        assert body["error"] == "unauthorized"
        assert "detail" in body
        assert body["code"] == "401"

    def test_login_when_missing_fields_returns_400(self, api_client):
        # Arrange
        payload = {"gmail": "admin@tsi.com"}

        # Act
        response = api_client.post("/api/v1/auth/login", payload, format="json")

        # Assert
        assert response.status_code == 400
        assert response.json()["error"] == "bad_request"
