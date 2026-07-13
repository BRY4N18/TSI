import pytest


@pytest.mark.api
class TestAuthLogoutContract:
    def test_logout_when_authenticated_closes_session(self, api_client, auth_headers):
        # Arrange / Act
        response = api_client.post("/api/v1/auth/logout", format="json", **auth_headers)

        # Assert
        assert response.status_code == 200
        body = response.json()
        assert "data" in body
        assert body["data"]["status"] == "Cierre sesion"
        assert "closedAt" in body["data"]

    def test_logout_when_unauthenticated_returns_401(self, api_client):
        # Arrange / Act
        response = api_client.post("/api/v1/auth/logout", format="json")

        # Assert
        assert response.status_code == 401
