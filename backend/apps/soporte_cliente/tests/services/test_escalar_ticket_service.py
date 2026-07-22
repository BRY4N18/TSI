import pytest

from apps.soporte_cliente.services.escalar_ticket_service import EscalarTicketService
from apps.soporte_cliente.services.registrar_ticket_service import RegistrarTicketService


@pytest.mark.service
class TestEscalarTicketService:
    def test_escalar_when_valid_pasa_a_escalado(self, mock_pinot, mock_kafka):
        # Arrange
        reclamo = RegistrarTicketService().registrar(
            idcliente=1, asunto="a", descripcion="b", tipo="tecnico", idusuario=3
        )

        # Act
        actualizado = EscalarTicketService().escalar(
            reclamo["id_reclamo"],
            id_rol_escalar="desarrollador_apis",
            id_agente_asignado=11,
            mensaje="Requiere revisión de API",
            idusuario=10,
        )

        # Assert
        assert actualizado["estado"] == "Escalado"
        assert actualizado["id_agente_asignado"] == 11

    def test_escalar_when_rol_invalido_raises(self, mock_pinot, mock_kafka):
        # Arrange
        reclamo = RegistrarTicketService().registrar(
            idcliente=1, asunto="a", descripcion="b", tipo="tecnico", idusuario=3
        )

        # Act / Assert
        with pytest.raises(ValueError):
            EscalarTicketService().escalar(
                reclamo["id_reclamo"], id_rol_escalar="invalido", id_agente_asignado=11
            )
