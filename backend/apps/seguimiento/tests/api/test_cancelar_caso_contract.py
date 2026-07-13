import pytest

from apps.accidentes.domain_constants import ESTADO_CERRADO


@pytest.mark.api
class TestCancelarCasoContract:
    def test_post_cancelar_when_motivo_returns_200(
        self,
        api_client,
        operador_seguimiento_auth_headers,
        accidente_activo,
        despacho_confirmado_unidad,
    ):
        # Arrange
        payload = {"motivo": "Falsa alarma reportada por testigo"}

        # Act
        response = api_client.post(
            f"/api/v1/accidentes/{accidente_activo}/cancelar",
            payload,
            format="json",
            **operador_seguimiento_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        body = response.json()
        assert body["data"]["estado_caso"] == ESTADO_CERRADO

    def test_post_cancelar_when_sin_motivo_returns_400(
        self,
        api_client,
        operador_seguimiento_auth_headers,
        accidente_activo,
        despacho_confirmado_unidad,
    ):
        # Arrange

        # Act
        response = api_client.post(
            f"/api/v1/accidentes/{accidente_activo}/cancelar",
            {},
            format="json",
            **operador_seguimiento_auth_headers,
        )

        # Assert
        assert response.status_code == 400
