import pytest

from apps.soporte_cliente.services.confirmar_cierre_service import ConfirmarCierreService
from apps.soporte_cliente.services.registrar_ticket_service import RegistrarTicketService
from apps.soporte_cliente.services.resolver_ticket_service import ResolverTicketService
from apps.soporte_cliente.services.tomar_ticket_service import TomarTicketService
from core.jwt_utils import create_access_token


def _ticket_cerrado():
    reclamo = RegistrarTicketService().registrar(
        idcliente=1, asunto="La API no responde", descripcion="error 500", tipo="tecnico", idusuario=3
    )
    TomarTicketService().tomar(reclamo["id_reclamo"], id_agente_asignado=10)
    ResolverTicketService().resolver(reclamo["id_reclamo"], idusuario=10)
    return ConfirmarCierreService().confirmar(reclamo["id_reclamo"], idcliente=1, idusuario=3)["id_reclamo"]


@pytest.mark.api
class TestReabrirTicketContract:
    def test_reabrir_when_cliente_returns_200(self, api_client, cliente_auth_headers):
        # Arrange
        id_reclamo = _ticket_cerrado()

        # Act
        response = api_client.post(
            f"/api/v1/soporte/tickets/{id_reclamo}/reabrir",
            {"motivo": "No quedó resuelto"},
            format="multipart",
            **cliente_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["data"]["estado_nuevo"] == "Reabierto"

    def test_reabrir_when_no_cerrado_returns_422(self, api_client, cliente_auth_headers):
        # Arrange
        reclamo = RegistrarTicketService().registrar(
            idcliente=1, asunto="La API no responde", descripcion="error 500", tipo="tecnico", idusuario=3
        )

        # Act
        response = api_client.post(
            f"/api/v1/soporte/tickets/{reclamo['id_reclamo']}/reabrir",
            format="multipart",
            **cliente_auth_headers,
        )

        # Assert
        assert response.status_code == 422

    def test_reabrir_when_otro_cliente_returns_403(
        self, api_client, mock_pinot, mock_kafka, pinot_store
    ):
        # Arrange — RF-O88.1: solo el cliente dueño del ticket puede reabrirlo
        id_reclamo = _ticket_cerrado()
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
            f"/api/v1/soporte/tickets/{id_reclamo}/reabrir",
            {"motivo": "No es mi ticket"},
            format="multipart",
            **otro_cliente_headers,
        )

        # Assert
        assert response.status_code == 403
