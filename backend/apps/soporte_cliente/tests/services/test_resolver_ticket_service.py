from datetime import datetime, timezone

import pytest

from apps.soporte_cliente.services.registrar_ticket_service import RegistrarTicketService
from apps.soporte_cliente.services.resolver_ticket_service import ResolverTicketService
from apps.soporte_cliente.services.tomar_ticket_service import TomarTicketService
from core.repositories.soporte.reclamo_repository import ReclamoRepository


@pytest.mark.service
class TestResolverTicketService:
    def test_resolver_when_dentro_de_plazo_marca_cumplido(self, mock_pinot, mock_kafka):
        # Arrange
        reclamo = RegistrarTicketService().registrar(
            idcliente=1, asunto="API caída", descripcion="error 500", tipo="tecnico", idusuario=3
        )
        TomarTicketService().tomar(reclamo["id_reclamo"], id_agente_asignado=10)

        # Act
        actualizado = ResolverTicketService().resolver(reclamo["id_reclamo"], idusuario=10)

        # Assert
        assert actualizado["estado"] == "Resuelto"
        assert actualizado["sla_status"] == "cumplido"

    def test_resolver_when_fuera_de_plazo_marca_incumplido(self, mock_pinot, mock_kafka):
        # Arrange
        reclamo = RegistrarTicketService().registrar(
            idcliente=1, asunto="API caída", descripcion="error 500", tipo="tecnico", idusuario=3
        )
        TomarTicketService().tomar(reclamo["id_reclamo"], id_agente_asignado=10)
        pasado = int(datetime.now(timezone.utc).timestamp() * 1000) - 1000
        ReclamoRepository().update(reclamo["id_reclamo"], {"sla_resolucion": pasado})

        # Act
        actualizado = ResolverTicketService().resolver(reclamo["id_reclamo"], idusuario=10)

        # Assert
        assert actualizado["sla_status"] == "incumplido"

    def test_resolver_when_pendiente_de_clasificacion_raises(self, mock_pinot, mock_kafka):
        # Arrange
        reclamo = RegistrarTicketService().registrar(
            idcliente=1, asunto="xyz", descripcion="qwerty", tipo="otro", idusuario=3
        )

        # Act / Assert
        with pytest.raises(ValueError):
            ResolverTicketService().resolver(reclamo["id_reclamo"], idusuario=10)
