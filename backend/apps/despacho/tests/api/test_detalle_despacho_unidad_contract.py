import pytest


@pytest.mark.api
class TestDetalleDespachoUnidadContract:
    def test_detalle_when_own_notificacion_returns_200(
        self,
        api_client,
        unidad_auth_headers,
        accidente_activo,
        unidad_con_estado_activa,
        despacho_pendiente_unidad,
    ):
        # Arrange
        idnotif = despacho_pendiente_unidad["idnotificaciondespacho"]

        # Act
        response = api_client.get(
            f"/api/v1/mi-despacho/{idnotif}",
            **unidad_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        body = response.json()
        assert body["data"]["idnotificaciondespacho"] == idnotif
        assert body["data"]["idaccidente"] == accidente_activo
