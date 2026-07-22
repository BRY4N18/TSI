import pytest

from apps.soporte_cliente.services.registrar_ticket_service import RegistrarTicketService
from apps.soporte_cliente.services.tomar_ticket_service import TomarTicketService


@pytest.mark.service
class TestTomarTicketService:
    def test_tomar_when_abierto_pasa_a_en_progreso(self, mock_pinot, mock_kafka):
        # Arrange
        reclamo = RegistrarTicketService().registrar(
            idcliente=1, asunto="API caída", descripcion="error 500", tipo="tecnico", idusuario=3
        )

        # Act
        actualizado = TomarTicketService().tomar(reclamo["id_reclamo"], id_agente_asignado=10)

        # Assert
        assert actualizado["estado"] == "En_progreso"
        assert actualizado["id_agente_asignado"] == 10

    def test_tomar_when_ya_en_progreso_raises(self, mock_pinot, mock_kafka):
        # Arrange
        reclamo = RegistrarTicketService().registrar(
            idcliente=1, asunto="API caída", descripcion="error 500", tipo="tecnico", idusuario=3
        )
        TomarTicketService().tomar(reclamo["id_reclamo"], id_agente_asignado=10)

        # Act / Assert
        with pytest.raises(ValueError):
            TomarTicketService().tomar(reclamo["id_reclamo"], id_agente_asignado=10)

    def test_tomar_when_not_found_raises(self, mock_pinot, mock_kafka):
        # Act / Assert
        with pytest.raises(LookupError):
            TomarTicketService().tomar(999, id_agente_asignado=10)
