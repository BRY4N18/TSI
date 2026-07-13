import pytest


@pytest.mark.api
class TestPasswordResetContract:
    def test_password_reset_when_valid_email_returns_envelope(self, api_client):
        # Arrange
        payload = {"gmail": "admin@tsi.com"}

        # Act
        response = api_client.post("/api/v1/auth/password-reset", payload, format="json")

        # Assert
        assert response.status_code == 200
        body = response.json()
        assert "data" in body
        assert body["data"]["credentialStatus"] == "Cambio contraseña"
        assert body["data"]["message"] == "Password reset email sent"

    def test_password_reset_when_unknown_email_returns_401(self, api_client):
        # Arrange
        payload = {"gmail": "nobody@tsi.com"}

        # Act
        response = api_client.post("/api/v1/auth/password-reset", payload, format="json")

        # Assert
        assert response.status_code == 401
        assert response.json()["error"] == "unauthorized"

    def test_password_reset_when_missing_gmail_returns_400(self, api_client):
        # Arrange / Act
        response = api_client.post("/api/v1/auth/password-reset", {}, format="json")

        # Assert
        assert response.status_code == 400
