import pytest


@pytest.mark.api
class TestMiSeguimientoActualContract:
    def test_get_actual_when_despacho_confirmado_returns_it(
        self,
        api_client,
        unidad_seguimiento_auth_headers,
        despacho_confirmado_unidad,
    ):
        # Arrange
        iddespacho = despacho_confirmado_unidad["iddespacho"]

        # Act
        response = api_client.get(
            "/api/v1/mi-seguimiento/actual",
            **unidad_seguimiento_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        body = response.json()["data"]["despacho"]
        assert body["iddespacho"] == iddespacho
        assert body["estado_despacho"] == "Confirmado"

    def test_get_actual_when_no_despacho_activo_returns_null(
        self,
        api_client,
        unidad_seguimiento_auth_headers,
        unidad_con_estado_activa,
    ):
        # Act
        response = api_client.get(
            "/api/v1/mi-seguimiento/actual",
            **unidad_seguimiento_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["data"]["despacho"] is None
