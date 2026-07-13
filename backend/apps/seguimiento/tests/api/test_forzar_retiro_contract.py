import pytest

from apps.seguimiento.services.registrar_llegada_service import RegistrarLlegadaService


@pytest.mark.api
class TestForzarRetiroContract:
    def test_post_forzar_retiro_when_en_atencion_returns_200(
        self,
        api_client,
        operador_seguimiento_auth_headers,
        accidente_activo,
        despacho_confirmado_unidad,
    ):
        # Arrange
        iddespacho = despacho_confirmado_unidad["iddespacho"]
        RegistrarLlegadaService().registrar(
            iddespacho=iddespacho,
            idunidademergencia=1,
            idusuario=6,
        )

        # Act
        response = api_client.post(
            f"/api/v1/despachos/{iddespacho}/forzar-retiro",
            {},
            format="json",
            **operador_seguimiento_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        body = response.json()
        assert body["data"]["iddespacho"] == iddespacho
        assert body["data"]["fechahoraretiro"] is not None

    def test_post_forzar_retiro_when_not_found_returns_404(
        self,
        api_client,
        operador_seguimiento_auth_headers,
    ):
        # Arrange

        # Act
        response = api_client.post(
            "/api/v1/despachos/99999/forzar-retiro",
            {},
            format="json",
            **operador_seguimiento_auth_headers,
        )

        # Assert
        assert response.status_code == 404
