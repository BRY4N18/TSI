import pytest

from apps.soporte_cliente.services.registrar_ticket_service import RegistrarTicketService


@pytest.mark.api
class TestEscalarTicketContract:
    def test_escalar_when_agente_returns_200(self, api_client, agente_soporte_auth_headers):
        # Arrange
        reclamo = RegistrarTicketService().registrar(
            idcliente=1, asunto="a", descripcion="b", tipo="tecnico", idusuario=3
        )

        # Act
        response = api_client.post(
            f"/api/v1/soporte/tickets/{reclamo['id_reclamo']}/escalar",
            {"id_rol_escalar": "desarrollador_apis", "id_agente_asignado": 11},
            format="json",
            **agente_soporte_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["data"]["estado_nuevo"] == "Escalado"

    def test_escalar_when_sin_id_agente_returns_400(self, api_client, agente_soporte_auth_headers):
        # Arrange
        reclamo = RegistrarTicketService().registrar(
            idcliente=1, asunto="a", descripcion="b", tipo="tecnico", idusuario=3
        )

        # Act
        response = api_client.post(
            f"/api/v1/soporte/tickets/{reclamo['id_reclamo']}/escalar",
            {"id_rol_escalar": "desarrollador_apis"},
            format="json",
            **agente_soporte_auth_headers,
        )

        # Assert
        assert response.status_code == 400

    def test_escalar_when_no_existe_returns_404(self, api_client, agente_soporte_auth_headers):
        # Act
        response = api_client.post(
            "/api/v1/soporte/tickets/999/escalar",
            {"id_rol_escalar": "desarrollador_apis", "id_agente_asignado": 11},
            format="json",
            **agente_soporte_auth_headers,
        )

        # Assert
        assert response.status_code == 404
