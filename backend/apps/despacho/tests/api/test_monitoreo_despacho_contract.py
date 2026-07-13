import pytest


@pytest.mark.api
class TestMonitoreoDespachoContract:
    def test_obtener_estado_when_operador_returns_200(
        self,
        api_client,
        operador_despacho_auth_headers,
        accidente_activo,
        despacho_pendiente_unidad,
    ):
        # Act
        response = api_client.get(
            f"/api/v1/accidentes/{accidente_activo}/despacho",
            **operador_despacho_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        body = response.json()
        assert body["data"]["idaccidente"] == accidente_activo
