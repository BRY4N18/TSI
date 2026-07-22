import pytest

from apps.soporte_cliente.services.registrar_ticket_service import RegistrarTicketService
from apps.soporte_cliente.services.resolver_ticket_service import ResolverTicketService
from apps.soporte_cliente.services.tomar_ticket_service import TomarTicketService


@pytest.mark.api
class TestConfirmarCierreContract:
    def test_confirmar_cierre_when_cliente_returns_200(self, api_client, cliente_auth_headers):
        # Arrange
        reclamo = RegistrarTicketService().registrar(
            idcliente=1, asunto="La API no responde", descripcion="error 500 constante", tipo="tecnico", idusuario=3
        )
        TomarTicketService().tomar(reclamo["id_reclamo"], id_agente_asignado=10)
        ResolverTicketService().resolver(reclamo["id_reclamo"], idusuario=10)

        # Act
        response = api_client.post(
            f"/api/v1/soporte/tickets/{reclamo['id_reclamo']}/confirmar-cierre",
            format="json",
            **cliente_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["data"]["estado_nuevo"] == "Cerrado"

    def test_confirmar_cierre_when_no_resuelto_returns_422(self, api_client, cliente_auth_headers):
        # Arrange
        reclamo = RegistrarTicketService().registrar(
            idcliente=1, asunto="La API no responde", descripcion="error 500 constante", tipo="tecnico", idusuario=3
        )

        # Act
        response = api_client.post(
            f"/api/v1/soporte/tickets/{reclamo['id_reclamo']}/confirmar-cierre",
            format="json",
            **cliente_auth_headers,
        )

        # Assert
        assert response.status_code == 422

    def test_confirmar_cierre_when_no_existe_returns_404(self, api_client, cliente_auth_headers):
        # Act
        response = api_client.post(
            "/api/v1/soporte/tickets/999/confirmar-cierre", format="json", **cliente_auth_headers
        )

        # Assert
        assert response.status_code == 404
