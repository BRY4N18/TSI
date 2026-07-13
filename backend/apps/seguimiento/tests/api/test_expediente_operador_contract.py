import pytest

from apps.seguimiento.services.cerrar_caso_service import CerrarCasoService
from apps.seguimiento.services.registrar_llegada_service import RegistrarLlegadaService


@pytest.mark.api
class TestExpedienteOperadorContract:
    def test_get_expediente_when_cerrado_returns_200(
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
            payload={"resultado_atencion": "Expediente operador test"},
        )

        # Act
        response = api_client.get(
            f"/api/v1/emergencias/historial/{accidente_activo}/expediente",
            **operador_seguimiento_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        body = response.json()
        assert body["data"]["accidente"]["idaccidente"] == accidente_activo
        assert "despachos" in body["data"]

    def test_get_expediente_when_not_found_returns_404(
        self,
        api_client,
        operador_seguimiento_auth_headers,
    ):
        # Arrange

        # Act
        response = api_client.get(
            "/api/v1/emergencias/historial/ACC-INEXISTENTE/expediente",
            **operador_seguimiento_auth_headers,
        )

        # Assert
        assert response.status_code == 404
