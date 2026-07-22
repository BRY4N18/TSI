import pytest

from apps.soporte_cliente.services.confirmar_cierre_service import ConfirmarCierreService
from apps.soporte_cliente.services.registrar_ticket_service import RegistrarTicketService
from apps.soporte_cliente.services.resolver_ticket_service import ResolverTicketService
from apps.soporte_cliente.services.tomar_ticket_service import TomarTicketService


def _ticket_cerrado():
    reclamo = RegistrarTicketService().registrar(
        idcliente=1, asunto="La API no responde", descripcion="error 500", tipo="tecnico", idusuario=3
    )
    TomarTicketService().tomar(reclamo["id_reclamo"], id_agente_asignado=10)
    ResolverTicketService().resolver(reclamo["id_reclamo"], idusuario=10)
    return ConfirmarCierreService().confirmar(reclamo["id_reclamo"], idusuario=3)["id_reclamo"]


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
