import pytest

from apps.soporte_cliente.services.registrar_ticket_service import RegistrarTicketService


@pytest.mark.api
class TestTomarTicketContract:
    def test_tomar_when_agente_returns_200(self, api_client, agente_soporte_auth_headers):
        # Arrange
        reclamo = RegistrarTicketService().registrar(
            idcliente=1, asunto="La API no responde", descripcion="error 500 constante", tipo="tecnico", idusuario=3
        )

        # Act
        response = api_client.post(
            f"/api/v1/soporte/tickets/{reclamo['id_reclamo']}/tomar",
            format="json",
            **agente_soporte_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["data"]["estado_nuevo"] == "En_progreso"

    def test_tomar_when_cliente_returns_403(self, api_client, cliente_auth_headers):
        # Arrange
        reclamo = RegistrarTicketService().registrar(
            idcliente=1, asunto="La API no responde", descripcion="error 500 constante", tipo="tecnico", idusuario=3
        )

        # Act
        response = api_client.post(
            f"/api/v1/soporte/tickets/{reclamo['id_reclamo']}/tomar",
            format="json",
            **cliente_auth_headers,
        )

        # Assert
        assert response.status_code == 403

    def test_tomar_when_no_existe_returns_404(self, api_client, agente_soporte_auth_headers):
        # Act
        response = api_client.post(
            "/api/v1/soporte/tickets/999/tomar", format="json", **agente_soporte_auth_headers
        )

        # Assert
        assert response.status_code == 404
