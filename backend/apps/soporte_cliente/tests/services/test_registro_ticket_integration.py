import pytest

from apps.soporte_cliente.services.registrar_ticket_service import RegistrarTicketService
from core.repositories.soporte.historial_ticket_repository import HistorialTicketRepository


@pytest.mark.service
class TestRegistroTicketIntegration:
    """Cruza RegistrarTicketService + ClasificacionAutomaticaService + AsignacionSLAService
    con Pinot/Kafka mockeados (marker `service`, no `integration` — ese marker está
    reservado en testing.md para infra real vía docker-compose)."""

    def test_registro_end_to_end_cuando_clasificable(self, mock_pinot, mock_kafka):
        # Arrange
        service = RegistrarTicketService()

        # Act
        reclamo = service.registrar(
            idcliente=1,
            asunto="Login no funciona",
            descripcion="No puedo acceder con mi contraseña",
            tipo="acceso",
            idusuario=3,
        )
        historial = HistorialTicketRepository().list_by_ticket(reclamo["id_reclamo"])

        # Assert
        assert reclamo["estado"] == "Abierto"
        assert reclamo["tipo_incidencia"] == "acceso"
        assert reclamo["sla_status"] == "en curso"
        assert len(historial) == 1
        assert historial[0]["tipo_accion"] == "creacion"

    def test_registro_end_to_end_cuando_no_clasificable_y_clasificacion_manual(
        self, mock_pinot, mock_kafka
    ):
        # Arrange
        service = RegistrarTicketService()
        reclamo = service.registrar(
            idcliente=1, asunto="xyz", descripcion="qwerty", tipo="otro", idusuario=3
        )

        # Act
        actualizado = service.clasificar_manual(
            reclamo["id_reclamo"], tipo_incidencia="tecnica", prioridad="alta", idusuario=10
        )

        # Assert
        assert actualizado["estado"] == "Abierto"
        assert actualizado["sla_status"] == "en curso"
