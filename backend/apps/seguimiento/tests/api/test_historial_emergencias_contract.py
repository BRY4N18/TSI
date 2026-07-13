import pytest

from apps.accidentes.domain_constants import ESTADO_CERRADO
from apps.seguimiento.services.cerrar_caso_service import CerrarCasoService
from apps.seguimiento.services.registrar_llegada_service import RegistrarLlegadaService


@pytest.mark.api
class TestHistorialEmergenciasContract:
    def test_get_historial_when_operador_returns_200(
        self,
        api_client,
        operador_seguimiento_auth_headers,
        accidente_activo,
        despacho_confirmado_unidad,
    ):
        # Arrange
        iddespacho = despacho_confirmado_unidad["iddespacho"]
        RegistrarLlegadaService().registrar(iddespacho=iddespacho, idunidademergencia=1, idusuario=6)
        CerrarCasoService().cerrar(
            idaccidente=accidente_activo,
            idusuario=2,
            payload={"resultado_atencion": "Cierre test historial"},
        )

        # Act
        response = api_client.get(
            "/api/v1/emergencias/historial",
            **operador_seguimiento_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        body = response.json()
        assert "items" in body["data"]
        assert any(i["idaccidente"] == accidente_activo for i in body["data"]["items"])

    def test_get_historial_when_unidad_returns_403(
        self,
        api_client,
        unidad_seguimiento_auth_headers,
    ):
        # Arrange

        # Act
        response = api_client.get(
            "/api/v1/emergencias/historial",
            **unidad_seguimiento_auth_headers,
        )

        # Assert
        assert response.status_code == 403
