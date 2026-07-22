import pytest

from apps.soporte_cliente.services.registrar_ticket_service import RegistrarTicketService
from apps.soporte_cliente.services.tomar_ticket_service import TomarTicketService


@pytest.mark.api
class TestResolverTicketContract:
    def test_resolver_when_agente_returns_200(self, api_client, agente_soporte_auth_headers):
        # Arrange
        reclamo = RegistrarTicketService().registrar(
            idcliente=1, asunto="La API no responde", descripcion="error 500 constante", tipo="tecnico", idusuario=3
        )
        TomarTicketService().tomar(reclamo["id_reclamo"], id_agente_asignado=10)

        # Act
        response = api_client.post(
            f"/api/v1/soporte/tickets/{reclamo['id_reclamo']}/resolver",
            {"mensaje": "Solucionado"},
            format="json",
            **agente_soporte_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["data"]["estado_nuevo"] == "Resuelto"

    def test_resolver_when_desarrollador_apis_returns_200(
        self, api_client, desarrollador_apis_auth_headers
    ):
        # Arrange
        reclamo = RegistrarTicketService().registrar(
            idcliente=1, asunto="La API no responde", descripcion="error 500 constante", tipo="tecnico", idusuario=3
        )
        TomarTicketService().tomar(reclamo["id_reclamo"], id_agente_asignado=10)

        # Act
        response = api_client.post(
            f"/api/v1/soporte/tickets/{reclamo['id_reclamo']}/resolver",
            {},
            format="json",
            **desarrollador_apis_auth_headers,
        )

        # Assert
        assert response.status_code == 200

    def test_resolver_when_cliente_returns_403(self, api_client, cliente_auth_headers):
        # Arrange
        reclamo = RegistrarTicketService().registrar(
            idcliente=1, asunto="La API no responde", descripcion="error 500 constante", tipo="tecnico", idusuario=3
        )

        # Act
        response = api_client.post(
            f"/api/v1/soporte/tickets/{reclamo['id_reclamo']}/resolver",
            {},
            format="json",
            **cliente_auth_headers,
        )

        # Assert
        assert response.status_code == 403

    def test_resolver_when_no_existe_returns_404(self, api_client, agente_soporte_auth_headers):
        # Act
        response = api_client.post(
            "/api/v1/soporte/tickets/999/resolver", {}, format="json", **agente_soporte_auth_headers
        )

        # Assert
        assert response.status_code == 404
