import pytest


@pytest.mark.api
class TestMapaSeguimientoContract:
    def test_get_mapa_when_operador_returns_200(
        self,
        api_client,
        operador_seguimiento_auth_headers,
        accidente_activo,
        despacho_confirmado_unidad,
    ):
        # Arrange — accidente activo con despacho confirmado

        # Act
        response = api_client.get(
            "/api/v1/seguimiento/mapa",
            **operador_seguimiento_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        body = response.json()
        assert "accidentes_activos" in body["data"]
        assert "unidades" in body["data"]
        assert any(a["idaccidente"] == accidente_activo for a in body["data"]["accidentes_activos"])

    def test_get_mapa_when_unidad_returns_403(
        self,
        api_client,
        unidad_seguimiento_auth_headers,
    ):
        # Arrange

        # Act
        response = api_client.get(
            "/api/v1/seguimiento/mapa",
            **unidad_seguimiento_auth_headers,
        )

        # Assert
        assert response.status_code == 403
