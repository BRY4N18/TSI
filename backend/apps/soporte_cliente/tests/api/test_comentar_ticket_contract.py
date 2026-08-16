import pytest

from apps.soporte_cliente.services.registrar_ticket_service import RegistrarTicketService
from core.jwt_utils import create_access_token


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

    def test_comentar_when_otro_cliente_returns_403(
        self, api_client, mock_pinot, mock_kafka, pinot_store
    ):
        # Arrange — el Cliente solo puede comentar sus propios tickets; agentes sí pueden en cualquiera.
        reclamo = RegistrarTicketService().registrar(
            idcliente=1, asunto="a", descripcion="b", tipo="tecnico", idusuario=3
        )
        pinot_store["Dim_Usuario_Cliente"].append({"idusuario": 999, "idcliente": 2, "activo": True})
        token = create_access_token(user_id=999, roles=["Cliente"], session_id=999)
        pinot_store["Fact_Session"].append(
            {
                "idsession": 999,
                "idusuario": 999,
                "token": "session-token-999",
                "refresh_token": "refresh-token-999",
                "navegador": "pytest",
                "fechahorainiciosesion": 1767225600000,
                "fechahoracierresesion": None,
                "estadosession": "Inicio sesion",
            }
        )
        otro_cliente_headers = {"HTTP_AUTHORIZATION": f"Bearer {token}"}

        # Act
        response = api_client.post(
            f"/api/v1/soporte/tickets/{reclamo['id_reclamo']}/comentarios",
            {"mensaje": "no es mi ticket"},
            format="json",
            **otro_cliente_headers,
        )

        # Assert
        assert response.status_code == 403
