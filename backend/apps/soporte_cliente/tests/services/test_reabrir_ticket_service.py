import pytest

from apps.soporte_cliente.services.confirmar_cierre_service import ConfirmarCierreService
from apps.soporte_cliente.services.reabrir_ticket_service import ReabrirTicketService
from apps.soporte_cliente.services.registrar_ticket_service import RegistrarTicketService
from apps.soporte_cliente.services.resolver_ticket_service import ResolverTicketService
from apps.soporte_cliente.services.tomar_ticket_service import TomarTicketService
from core.repositories.soporte.historial_ticket_repository import HistorialTicketRepository


def _ticket_cerrado():
    reclamo = RegistrarTicketService().registrar(
        idcliente=1, asunto="La API no responde", descripcion="error 500", tipo="tecnico", idusuario=3
    )
    TomarTicketService().tomar(reclamo["id_reclamo"], id_agente_asignado=10)
    ResolverTicketService().resolver(reclamo["id_reclamo"], idusuario=10)
    return ConfirmarCierreService().confirmar(reclamo["id_reclamo"], idusuario=3)["id_reclamo"]


@pytest.mark.service
class TestReabrirTicketService:
    def test_reabrir_when_cerrado_renueva_sla_y_conserva_historial(self, mock_pinot, mock_kafka):
        # Arrange
        id_reclamo = _ticket_cerrado()
        historial_previo = HistorialTicketRepository().list_by_ticket(id_reclamo)

        # Act
        actualizado = ReabrirTicketService().reabrir(id_reclamo, idusuario=3, motivo="No quedó resuelto")
        historial_nuevo = HistorialTicketRepository().list_by_ticket(id_reclamo)

        # Assert
        assert actualizado["estado"] == "Reabierto"
        assert actualizado["sla_status"] == "en curso"
        assert len(historial_nuevo) == len(historial_previo) + 1
        assert historial_nuevo[-1]["tipo_accion"] == "reapertura"

    def test_reabrir_when_no_cerrado_raises(self, mock_pinot, mock_kafka):
        # Arrange
        reclamo = RegistrarTicketService().registrar(
            idcliente=1, asunto="La API no responde", descripcion="error 500", tipo="tecnico", idusuario=3
        )

        # Act / Assert
        with pytest.raises(ValueError):
            ReabrirTicketService().reabrir(reclamo["id_reclamo"], idusuario=3)

    def test_reabrir_when_adjunto_publica_archivo(self, mock_pinot, mock_kafka, tmp_path):
        # Arrange
        from core.storage.blob_storage_service import BlobStorageService

        id_reclamo = _ticket_cerrado()
        contenido = b"\xff\xd8\xff\xe0fake-jpeg-bytes"
        service = ReabrirTicketService(blob_storage=BlobStorageService(base_path=tmp_path))

        # Act
        service.reabrir(id_reclamo, idusuario=3, adjuntos=[(contenido, "image/jpeg")])

        # Assert
        from core.repositories.soporte.archivo_adjunto_reclamo_repository import (
            ArchivoAdjuntoReclamoRepository,
        )

        adjuntos = ArchivoAdjuntoReclamoRepository().list_by_ticket(id_reclamo)
        assert len(adjuntos) == 1
