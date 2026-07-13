import pytest


@pytest.mark.api
class TestSeguimientoAccidenteContract:
    def test_get_seguimiento_when_operador_returns_200(
        self,
        api_client,
        operador_seguimiento_auth_headers,
        accidente_activo,
        despacho_confirmado_unidad,
    ):
        # Arrange

        # Act
        response = api_client.get(
            f"/api/v1/accidentes/{accidente_activo}/seguimiento",
            **operador_seguimiento_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        body = response.json()
        assert body["data"]["idaccidente"] == accidente_activo
        assert "despachos" in body["data"]
        assert len(body["data"]["despachos"]) >= 1

    def test_get_seguimiento_when_not_found_returns_404(
        self,
        api_client,
        operador_seguimiento_auth_headers,
    ):
        # Arrange

        # Act
        response = api_client.get(
            "/api/v1/accidentes/ACC-INEXISTENTE/seguimiento",
            **operador_seguimiento_auth_headers,
        )

        # Assert
        assert response.status_code == 404
