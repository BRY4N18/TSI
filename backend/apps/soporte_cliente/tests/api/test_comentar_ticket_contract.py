import pytest

from apps.soporte_cliente.services.registrar_ticket_service import RegistrarTicketService


@pytest.mark.api
class TestComentarTicketContract:
    def test_comentar_when_cliente_fuerza_nota_no_interna(self, api_client, cliente_auth_headers):
        # Arrange
        reclamo = RegistrarTicketService().registrar(
            idcliente=1, asunto="a", descripcion="b", tipo="tecnico", idusuario=3
        )

        # Act — un Cliente intentando marcar es_nota_interna=true no debe lograrlo (RN-TIC-002)
        response = api_client.post(
            f"/api/v1/soporte/tickets/{reclamo['id_reclamo']}/comentarios",
            {"mensaje": "¿Cuándo se resuelve?", "es_nota_interna": True},
            format="json",
            **cliente_auth_headers,
        )

        # Assert
        assert response.status_code == 201
        assert response.json()["data"]["es_nota_interna"] is False

    def test_comentar_when_sin_mensaje_returns_400(self, api_client, agente_soporte_auth_headers):
        # Arrange
        reclamo = RegistrarTicketService().registrar(
            idcliente=1, asunto="a", descripcion="b", tipo="tecnico", idusuario=3
        )

        # Act
        response = api_client.post(
            f"/api/v1/soporte/tickets/{reclamo['id_reclamo']}/comentarios",
            {},
            format="json",
            **agente_soporte_auth_headers,
        )

        # Assert
        assert response.status_code == 400

    def test_comentar_when_no_existe_returns_404(self, api_client, agente_soporte_auth_headers):
        # Act
        response = api_client.post(
            "/api/v1/soporte/tickets/999/comentarios",
            {"mensaje": "hola"},
            format="json",
            **agente_soporte_auth_headers,
        )

        # Assert
        assert response.status_code == 404
