import pytest

from apps.soporte_cliente.services.dashboard_soporte_service import DashboardSoporteService
from apps.soporte_cliente.services.registrar_ticket_service import RegistrarTicketService
from apps.soporte_cliente.services.tomar_ticket_service import TomarTicketService


@pytest.mark.service
class TestDashboardSoporteService:
    def test_metricas_when_tickets_existentes_agrega_correctamente(self, mock_pinot, mock_kafka):
        # Arrange
        t1 = RegistrarTicketService().registrar(
            idcliente=1, asunto="La API no responde", descripcion="error 500", tipo="tecnico", idusuario=3
        )
        RegistrarTicketService().registrar(
            idcliente=1, asunto="xyz", descripcion="qwerty", tipo="otro", idusuario=3
        )
        TomarTicketService().tomar(t1["id_reclamo"], id_agente_asignado=10)

        # Act
        metricas = DashboardSoporteService().metricas()

        # Assert
        assert metricas["total_tickets"] == 2
        assert metricas["por_estado"]["En_progreso"] == 1
        assert metricas["por_estado"]["Pendiente_de_clasificacion"] == 1
        assert metricas["tiempo_promedio_primera_respuesta_ms"] is not None

    def test_metricas_when_sin_tickets_returns_ceros(self, mock_pinot, mock_kafka):
        # Act
        metricas = DashboardSoporteService().metricas()

        # Assert
        assert metricas["total_tickets"] == 0
        assert metricas["tasa_reapertura"] == 0.0
