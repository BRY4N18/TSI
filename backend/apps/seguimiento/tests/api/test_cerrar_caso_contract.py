import pytest

from apps.accidentes.domain_constants import ESTADO_CERRADO, ESTADO_EN_ATENCION
from apps.seguimiento.services.registrar_llegada_service import RegistrarLlegadaService
from core.repositories.accidentes.estado_accidente_repository import EstadoAccidenteRepository


@pytest.mark.api
class TestCerrarCasoContract:
    def test_post_cerrar_when_en_atencion_returns_200(
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
        assert EstadoAccidenteRepository().get_current_estado(accidente_activo) == ESTADO_EN_ATENCION
        payload = {"resultado_atencion": "Atención completada sin novedad"}

        # Act
        response = api_client.post(
            f"/api/v1/accidentes/{accidente_activo}/cerrar",
            payload,
            format="json",
            **operador_seguimiento_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        body = response.json()
        assert body["data"]["estado_caso"] == ESTADO_CERRADO
        assert body["data"]["horafin"] is not None

    def test_post_cerrar_when_sin_resultado_returns_400(
        self,
        api_client,
        operador_seguimiento_auth_headers,
        accidente_activo,
        despacho_confirmado_unidad,
    ):
        # Arrange
        RegistrarLlegadaService().registrar(
            iddespacho=despacho_confirmado_unidad["iddespacho"],
            idunidademergencia=1,
            idusuario=6,
        )

        # Act
        response = api_client.post(
            f"/api/v1/accidentes/{accidente_activo}/cerrar",
            {},
            format="json",
            **operador_seguimiento_auth_headers,
        )

        # Assert
        assert response.status_code == 400
