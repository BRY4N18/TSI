import pytest

from apps.soporte_cliente.services.comentar_ticket_service import ComentarTicketService
from apps.soporte_cliente.services.registrar_ticket_service import RegistrarTicketService


@pytest.mark.service
class TestComentarTicketService:
    def test_comentar_when_valid_publishes(self, mock_pinot, mock_kafka):
        # Arrange
        reclamo = RegistrarTicketService().registrar(
            idcliente=1, asunto="a", descripcion="b", tipo="tecnico", idusuario=3
        )

        # Act
        comentario = ComentarTicketService().comentar(
            reclamo["id_reclamo"], mensaje="Investigando", es_nota_interna=True, idusuario=10
        )

        # Assert
        assert comentario["tipo_accion"] == "comentario"
        assert comentario["es_nota_interna"] is True

    def test_listar_para_rol_when_cliente_oculta_notas_internas(self, mock_pinot, mock_kafka):
        # Arrange — RN-TIC-002
        reclamo = RegistrarTicketService().registrar(
            idcliente=1, asunto="a", descripcion="b", tipo="tecnico", idusuario=3
        )
        service = ComentarTicketService()
        service.comentar(reclamo["id_reclamo"], mensaje="nota interna", es_nota_interna=True, idusuario=10)
        service.comentar(reclamo["id_reclamo"], mensaje="respuesta al cliente", es_nota_interna=False, idusuario=10)

        # Act
        visibles_cliente = service.listar_para_rol(reclamo["id_reclamo"], ocultar_notas_internas=True)
        visibles_agente = service.listar_para_rol(reclamo["id_reclamo"], ocultar_notas_internas=False)

        # Assert
        assert len(visibles_cliente) == 2  # creacion + respuesta (nota interna oculta)
        assert all(not h.get("es_nota_interna") for h in visibles_cliente)
        assert len(visibles_agente) == 3
