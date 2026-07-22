import pytest


@pytest.mark.api
class TestConfirmarDespachoContract:
    def test_confirmar_when_pendiente_returns_200(
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
        response = api_client.post(
            f"/api/v1/mi-despacho/{idnotif}/confirmar",
            {},
            format="json",
            **unidad_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        body = response.json()
        assert body["data"]["estado_unidad"] == "En Misión"
        assert body["data"]["estado_caso"] == "ASIGNADO"
        assert body["data"]["idunidademergencia"] == 1
