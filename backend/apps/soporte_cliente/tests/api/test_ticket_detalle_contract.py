import pytest

from apps.soporte_cliente.services.registrar_ticket_service import RegistrarTicketService
from core.jwt_utils import create_access_token


@pytest.mark.api
class TestTicketDetalleContract:
    def test_get_when_propio_cliente_returns_200(self, api_client, cliente_auth_headers):
        # Arrange
        reclamo = RegistrarTicketService().registrar(
            idcliente=1, asunto="La API no responde", descripcion="error 500", tipo="tecnico", idusuario=3
        )

        # Act
        response = api_client.get(
            f"/api/v1/soporte/tickets/{reclamo['id_reclamo']}", **cliente_auth_headers
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["data"]["ticket"]["id_reclamo"] == reclamo["id_reclamo"]

    def test_get_when_no_existe_returns_404(self, api_client, agente_soporte_auth_headers):
        # Act
        response = api_client.get("/api/v1/soporte/tickets/999", **agente_soporte_auth_headers)

        # Assert
        assert response.status_code == 404

    def test_get_when_cliente_ajeno_returns_403(self, api_client, mock_pinot, mock_kafka, pinot_store):
        # Arrange — usuario nuevo vinculado a idcliente=2 (no al dueño real, idcliente=1)
        pinot_store["Dim_Usuario_Cliente"].append({"idusuario": 12, "idcliente": 2, "activo": True})
        token = create_access_token(user_id=12, roles=["Cliente"], session_id=12)
        pinot_store["Fact_Session"].append(
            {
                "idsession": 12,
                "idusuario": 12,
                "token": "session-token-12",
                "refresh_token": "refresh-token-12",
                "navegador": "pytest",
                "fechahorainiciosesion": "2026-01-01T00:00:00+00:00",
                "fechahoracierresesion": None,
                "estadosession": "Inicio sesion",
            }
        )
        ajeno_auth_headers = {"HTTP_AUTHORIZATION": f"Bearer {token}"}
        reclamo = RegistrarTicketService().registrar(
            idcliente=1, asunto="La API no responde", descripcion="error 500", tipo="tecnico", idusuario=3
        )

        # Act
        response = api_client.get(
            f"/api/v1/soporte/tickets/{reclamo['id_reclamo']}", **ajeno_auth_headers
        )

        # Assert
        assert response.status_code == 403


@pytest.mark.api
class TestTicketsListContract:
    def test_get_when_cliente_returns_solo_propios(self, api_client, cliente_auth_headers):
        # Arrange
        RegistrarTicketService().registrar(
            idcliente=1, asunto="a", descripcion="b", tipo="tecnico", idusuario=3
        )
        RegistrarTicketService().registrar(
            idcliente=2, asunto="c", descripcion="d", tipo="tecnico", idusuario=5
        )

        # Act
        response = api_client.get("/api/v1/soporte/tickets", **cliente_auth_headers)

        # Assert
        assert response.status_code == 200
        items = response.json()["data"]["items"]
        assert all(i["idcliente"] == 1 for i in items)

    def test_get_when_agente_returns_todos(self, api_client, agente_soporte_auth_headers):
        # Arrange
        RegistrarTicketService().registrar(
            idcliente=1, asunto="a", descripcion="b", tipo="tecnico", idusuario=3
        )

        # Act
        response = api_client.get("/api/v1/soporte/tickets", **agente_soporte_auth_headers)

        # Assert
        assert response.status_code == 200
