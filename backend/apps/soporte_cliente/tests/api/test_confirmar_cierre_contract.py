import pytest

from apps.soporte_cliente.services.registrar_ticket_service import RegistrarTicketService
from apps.soporte_cliente.services.resolver_ticket_service import ResolverTicketService
from apps.soporte_cliente.services.tomar_ticket_service import TomarTicketService
from core.jwt_utils import create_access_token


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

    def test_confirmar_cierre_when_otro_cliente_returns_403(
        self, api_client, mock_pinot, mock_kafka, pinot_store
    ):
        # Arrange — RF-O87.1: solo el cliente dueño del ticket puede confirmar el cierre
        reclamo = RegistrarTicketService().registrar(
            idcliente=1, asunto="La API no responde", descripcion="error 500 constante", tipo="tecnico", idusuario=3
        )
        TomarTicketService().tomar(reclamo["id_reclamo"], id_agente_asignado=10)
        ResolverTicketService().resolver(reclamo["id_reclamo"], idusuario=10)
        pinot_store["Dim_Usuario_Cliente"].append({"idusuario": 999, "idcliente": 2, "activo": True})
        token = create_access_token(user_id=999, roles=["Cliente"], session_id=999)
        pinot_store["Fact_Session"].append(
            {
                "idsession": 999,
                "idusuario": 999,
                "token": "session-token-999",
                "refresh_token": "refresh-token-999",
                "navegador": "pytest",
                "fechahorainiciosesion": "2026-01-01T00:00:00+00:00",
                "fechahoracierresesion": None,
                "estadosession": "Inicio sesion",
            }
        )
        otro_cliente_headers = {"HTTP_AUTHORIZATION": f"Bearer {token}"}

        # Act
        response = api_client.post(
            f"/api/v1/soporte/tickets/{reclamo['id_reclamo']}/confirmar-cierre",
            format="json",
            **otro_cliente_headers,
        )

        # Assert
        assert response.status_code == 403
