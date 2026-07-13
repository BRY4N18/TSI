import pytest

from apps.seguimiento.services.cerrar_caso_service import CerrarCasoService
from apps.seguimiento.services.registrar_llegada_service import RegistrarLlegadaService


@pytest.mark.api
class TestExpedientePdfContract:
    def test_get_pdf_when_cerrado_returns_pdf(
        self,
        api_client,
        cliente_expediente_auth_headers,
        accidente_activo,
        despacho_confirmado_unidad,
    ):
        # Arrange
        iddespacho = despacho_confirmado_unidad["iddespacho"]
        RegistrarLlegadaService().registrar(iddespacho=iddespacho, idunidademergencia=1, idusuario=6)
        CerrarCasoService().cerrar(
            idaccidente=accidente_activo,
            idusuario=2,
            payload={"resultado_atencion": "PDF test"},
        )

        # Act
        response = api_client.get(
            f"/api/v1/cliente/expedientes/{accidente_activo}/pdf",
            **cliente_expediente_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        assert response["Content-Type"] == "application/pdf"
        assert response.content.startswith(b"%PDF")

    def test_get_pdf_when_activo_returns_404(
        self,
        api_client,
        cliente_expediente_auth_headers,
        accidente_activo,
        despacho_confirmado_unidad,
    ):
        # Arrange — caso aún activo sin cerrar

        # Act
        response = api_client.get(
            f"/api/v1/cliente/expedientes/{accidente_activo}/pdf",
            **cliente_expediente_auth_headers,
        )

        # Assert
        assert response.status_code == 404
