import pytest


@pytest.mark.api
class TestClienteSinMapaContract:
    def test_get_mapa_when_cliente_returns_403(
        self,
        api_client,
        cliente_expediente_auth_headers,
    ):
        # Arrange — CA-SEG-010: cliente no accede al mapa operador

        # Act
        response = api_client.get(
            "/api/v1/seguimiento/mapa",
            **cliente_expediente_auth_headers,
        )

        # Assert
        assert response.status_code == 403
