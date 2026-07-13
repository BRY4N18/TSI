import pytest


@pytest.mark.api
class TestConsultarMiDisponibilidadContract:
    def test_consultar_when_unidad_returns_200(self, api_client, unidad_auth_headers):
        # Act
        response = api_client.get(
            "/api/v1/mi-unidad-emergencia/disponibilidad",
            **unidad_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["idunidademergencia"] == 1
        assert data["estado_actual"] == "Fuera de servicio"
        assert data["incluido_en_despacho"] is False
