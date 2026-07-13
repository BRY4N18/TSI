import pytest


@pytest.mark.api
class TestAuthRevokeContract:
    def test_revoke_when_admin_revokes_session(self, api_client, auth_headers):
        # Arrange
        payload = {"idsession": 1}

        # Act
        response = api_client.post(
            "/api/v1/auth/revoke-session", payload, format="json", **auth_headers
        )

        # Assert
        assert response.status_code == 200
        body = response.json()
        assert body["data"]["status"] == "Expulsado"
        assert body["data"]["sessionId"] == 1

    def test_revoke_when_not_admin_returns_403(self, api_client, operator_auth_headers):
        # Arrange
        payload = {"idsession": 2}

        # Act
        response = api_client.post(
            "/api/v1/auth/revoke-session",
            payload,
            format="json",
            **operator_auth_headers,
        )

        # Assert
        assert response.status_code == 403
        assert response.json()["error"] == "forbidden"

    def test_revoke_when_missing_session_id_returns_400(self, api_client, auth_headers):
        # Arrange / Act
        response = api_client.post(
            "/api/v1/auth/revoke-session", {}, format="json", **auth_headers
        )

        # Assert
        assert response.status_code == 400
