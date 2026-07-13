import pytest

from apps.accidentes.domain_constants import ESTADO_EN_ATENCION


@pytest.mark.api
class TestRegistrarLlegadaContract:
    def test_post_llegada_when_confirmado_returns_200(
        self,
        api_client,
        unidad_seguimiento_auth_headers,
        despacho_confirmado_unidad,
    ):
        # Arrange
        iddespacho = despacho_confirmado_unidad["iddespacho"]

        # Act
        response = api_client.post(
            f"/api/v1/mi-seguimiento/despachos/{iddespacho}/llegada",
            {},
            format="json",
            **unidad_seguimiento_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        body = response.json()
        assert body["data"]["estado_caso"] == ESTADO_EN_ATENCION
        assert body["data"]["fechahorallegada"] is not None
