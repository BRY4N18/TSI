import pytest


@pytest.mark.api
class TestSeguimientoSseContract:
    def test_get_stream_when_operador_returns_event_stream(
        self,
        api_client,
        operador_seguimiento_auth_headers,
    ):
        # Arrange

        # Act
        response = api_client.get(
            "/api/v1/seguimiento/stream",
            **operador_seguimiento_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        assert response["Content-Type"] == "text/event-stream"
        first_chunk = next(response.streaming_content)
        assert b"connected" in first_chunk

    def test_get_stream_when_unidad_returns_403(
        self,
        api_client,
        unidad_seguimiento_auth_headers,
    ):
        # Arrange

        # Act
        response = api_client.get(
            "/api/v1/seguimiento/stream",
            **unidad_seguimiento_auth_headers,
        )

        # Assert
        assert response.status_code == 403
