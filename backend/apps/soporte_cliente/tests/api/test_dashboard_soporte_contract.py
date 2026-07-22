import pytest


@pytest.mark.api
class TestDashboardSoporteContract:
    def test_get_when_agente_returns_200(self, api_client, agente_soporte_auth_headers):
        # Act
        response = api_client.get("/api/v1/soporte/dashboard", **agente_soporte_auth_headers)

        # Assert
        assert response.status_code == 200
        assert "total_tickets" in response.json()["data"]

    def test_get_when_cliente_returns_403(self, api_client, cliente_auth_headers):
        # Act
        response = api_client.get("/api/v1/soporte/dashboard", **cliente_auth_headers)

        # Assert
        assert response.status_code == 403
