from datetime import datetime, timezone

import pytest

from apps.soporte_cliente.services.confirmar_cierre_service import ConfirmarCierreService
from apps.soporte_cliente.services.registrar_ticket_service import RegistrarTicketService
from apps.soporte_cliente.services.resolver_ticket_service import ResolverTicketService
from apps.soporte_cliente.services.tomar_ticket_service import TomarTicketService


def _registrar_y_resolver(idusuario_agente=10):
    reclamo = RegistrarTicketService().registrar(
        idcliente=1,
        asunto="La API no responde",
        descripcion="error 500 constante",
        tipo="tecnico",
        idusuario=3,
    )
    TomarTicketService().tomar(reclamo["id_reclamo"], id_agente_asignado=idusuario_agente)
    ResolverTicketService().resolver(reclamo["id_reclamo"], idusuario=idusuario_agente)
    return reclamo["id_reclamo"]


@pytest.mark.service
class TestConfirmarCierreService:
    def test_confirmar_when_resuelto_pasa_a_cerrado(self, mock_pinot, mock_kafka):
        # Arrange
        id_reclamo = _registrar_y_resolver()

        # Act
        actualizado = ConfirmarCierreService().confirmar(id_reclamo, idusuario=3)

        # Assert
        assert actualizado["estado"] == "Cerrado"
        assert actualizado["cierreconfirmadocliente"] is True

    def test_confirmar_when_no_resuelto_raises(self, mock_pinot, mock_kafka):
        # Arrange
        reclamo = RegistrarTicketService().registrar(
            idcliente=1, asunto="La API no responde", descripcion="error 500 constante", tipo="tecnico", idusuario=3
        )

        # Act / Assert
        with pytest.raises(ValueError):
            ConfirmarCierreService().confirmar(reclamo["id_reclamo"], idusuario=3)

    def test_cerrar_automaticamente_vencidos_cuando_pasaron_5_dias(
        self, mock_pinot, mock_kafka, pinot_store
    ):
        # Arrange — RN-TIC-004
        id_reclamo = _registrar_y_resolver()
        hace_6_dias = int(datetime.now(timezone.utc).timestamp() * 1000) - 6 * 24 * 60 * 60 * 1000
        for row in pinot_store["Fact_Reclamo"]:
            if row["id_reclamo"] == id_reclamo:
                row["fecha_actualizacion"] = hace_6_dias

        # Act
        cerrados = ConfirmarCierreService().cerrar_automaticamente_vencidos()

        # Assert
        assert len(cerrados) == 1
        assert cerrados[0]["cierreconfirmadocliente"] is False
        assert cerrados[0]["estado"] == "Cerrado"
