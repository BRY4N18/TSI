import pytest


@pytest.mark.api
class TestRegistrarPosicionContract:
    def test_post_posicion_when_confirmado_returns_202(
        self,
        api_client,
        unidad_seguimiento_auth_headers,
        accidente_activo,
        despacho_confirmado_unidad,
    ):
        # Arrange
        payload = {
            "idunidademergencia": 1,
            "idaccidente": accidente_activo,
            "latitud": 19.4326,
            "longitud": -99.1332,
            "fechahora": 1_700_000_000_000,
        }

        # Act
        response = api_client.post(
            "/api/v1/mi-seguimiento/posicion",
            payload,
            format="json",
            **unidad_seguimiento_auth_headers,
        )

        # Assert
        assert response.status_code == 202
        body = response.json()
        assert body["data"]["aceptado"] is True

    def test_post_posicion_when_unidad_mismatch_returns_403(
        self,
        api_client,
        unidad_seguimiento_auth_headers,
        accidente_activo,
        despacho_confirmado_unidad,
    ):
        # Arrange
        payload = {
            "idunidademergencia": 99,
            "idaccidente": accidente_activo,
            "latitud": 19.4326,
            "longitud": -99.1332,
            "fechahora": 1_700_000_000_000,
        }

        # Act
        response = api_client.post(
            "/api/v1/mi-seguimiento/posicion",
            payload,
            format="json",
            **unidad_seguimiento_auth_headers,
        )

        # Assert
        assert response.status_code == 403
