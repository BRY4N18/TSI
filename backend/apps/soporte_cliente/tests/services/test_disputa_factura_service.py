"""RF-O83.2 x RF-APM-014 — abrir una disputa excluye la factura del cobro."""

from __future__ import annotations

import pytest

from apps.partners.services.tarificacion_excedente_service import TarificacionExcedenteService
from apps.soporte_cliente.services.confirmar_cierre_service import ConfirmarCierreService
from apps.soporte_cliente.services.registrar_ticket_service import RegistrarTicketService
from core.repositories.soporte.reclamo_repository import ReclamoRepository
from core.repositories.suscripciones.factura_repository import FacturaRepository

TOPIC_FACTURA = "Fact_Factura_topic"


def _factura() -> dict:
    return FacturaRepository().create(
        {
            "id_cliente": 1,
            "id_suscripcion": 1,
            "periodo": "2026-08",
            "monto_base": 120.0,
            "desglose_cargos": [],
        }
    )


def _publicadas(mock_kafka, id_factura: str) -> list[dict]:
    # Se mira el payload PUBLICADO, no el doble: la tabla es upsert por PK y una
    # publicacion parcial borraria columnas en Pinot de verdad.
    return [
        msg["payload"]
        for msg in mock_kafka
        if msg["topic"].endswith(TOPIC_FACTURA)
        and msg["payload"]["id_factura"] == id_factura
    ]


@pytest.mark.service
class TestDisputaMarcaLaFactura:
    def test_registrar_ticket_con_idfactura_la_marca_en_disputa(self, mock_pinot, mock_kafka):
        # Arrange
        factura = _factura()

        # Act
        RegistrarTicketService().registrar(
            idcliente=1,
            asunto="Me cobraron un excedente que no consumi",
            descripcion="El detalle de llamadas no cuadra con el monto facturado",
            tipo="facturacion",
            idfactura=factura["id_factura"],
            idusuario=3,
        )

        # Assert — la ultima publicacion lleva el estado y la fila COMPLETA
        ultima = _publicadas(mock_kafka, factura["id_factura"])[-1]
        assert ultima["estado_pago"] == "En disputa"
        assert ultima["monto_total"] == 120.0
        assert ultima["numero_factura"] == factura["numero_factura"]

    def test_la_factura_en_disputa_queda_fuera_del_cobro_automatico(
        self, mock_pinot, mock_kafka
    ):
        # Arrange — es el efecto que exige RF-APM-014, no un detalle de columna
        factura = _factura()
        RegistrarTicketService().registrar(
            idcliente=1,
            asunto="Cargo indebido",
            descripcion="Discrepancia en el excedente",
            tipo="facturacion",
            idfactura=factura["id_factura"],
        )

        # Act
        vigente = FacturaRepository().find_by_id(factura["id_factura"])

        # Assert
        assert TarificacionExcedenteService().en_disputa(vigente) is True

    def test_cerrar_el_ticket_devuelve_la_factura_al_cobro_normal(
        self, mock_pinot, mock_kafka
    ):
        # Arrange
        factura = _factura()
        reclamo = RegistrarTicketService().registrar(
            idcliente=1,
            asunto="Cargo indebido",
            descripcion="Discrepancia en el excedente",
            tipo="facturacion",
            idfactura=factura["id_factura"],
        )
        repo = ReclamoRepository()
        repo.update(reclamo["id_reclamo"], {"estado": "Resuelto"})

        # Act
        ConfirmarCierreService().confirmar(reclamo["id_reclamo"], idcliente=1, idusuario=3)

        # Assert
        vigente = FacturaRepository().find_by_id(factura["id_factura"])
        assert vigente["estado_pago"] == "Pendiente"

    def test_cierre_automatico_tambien_libera_la_factura(
        self, mock_pinot, mock_kafka, pinot_store
    ):
        """Si solo liberase la confirmacion del cliente, un ticket auto-cerrado a
        los 5 dias dejaria la factura excluida del cobro para siempre."""
        # Arrange
        factura = _factura()
        reclamo = RegistrarTicketService().registrar(
            idcliente=1,
            asunto="Cargo indebido",
            descripcion="Discrepancia en el excedente",
            tipo="facturacion",
            idfactura=factura["id_factura"],
        )
        ReclamoRepository().update(reclamo["id_reclamo"], {"estado": "Resuelto"})
        # El repo sella `fecha_actualizacion` en cada update: para envejecer el
        # ticket hay que tocar la fila, no pasarla como cambio.
        for row in pinot_store["Fact_Reclamo"]:
            if row["id_reclamo"] == reclamo["id_reclamo"]:
                row["fecha_actualizacion"] = 0

        # Act
        ConfirmarCierreService().cerrar_automaticamente_vencidos()

        # Assert
        vigente = FacturaRepository().find_by_id(factura["id_factura"])
        assert vigente["estado_pago"] == "Pendiente"

    def test_liberar_no_pisa_una_factura_ya_pagada_en_la_resolucion(
        self, mock_pinot, mock_kafka
    ):
        """RF-APM-014 dice «pagada o con monto ajustado segun la resolucion»:
        devolverla a «Pendiente» volveria a cobrar lo ya resuelto."""
        # Arrange
        factura = _factura()
        reclamo = RegistrarTicketService().registrar(
            idcliente=1,
            asunto="Cargo indebido",
            descripcion="Discrepancia en el excedente",
            tipo="facturacion",
            idfactura=factura["id_factura"],
        )
        FacturaRepository().update(factura["id_factura"], {"estado_pago": "Pagada"})
        ReclamoRepository().update(reclamo["id_reclamo"], {"estado": "Resuelto"})

        # Act
        ConfirmarCierreService().confirmar(reclamo["id_reclamo"], idcliente=1, idusuario=3)

        # Assert
        vigente = FacturaRepository().find_by_id(factura["id_factura"])
        assert vigente["estado_pago"] == "Pagada"

    def test_ticket_sin_factura_no_toca_ninguna(self, mock_pinot, mock_kafka):
        # Arrange
        factura = _factura()
        publicadas_antes = len(_publicadas(mock_kafka, factura["id_factura"]))

        # Act
        RegistrarTicketService().registrar(
            idcliente=1,
            asunto="Login no funciona",
            descripcion="No puedo acceder",
            tipo="acceso",
        )

        # Assert
        assert len(_publicadas(mock_kafka, factura["id_factura"])) == publicadas_antes

    def test_la_segunda_disputa_nombra_el_ticket_que_ya_existe(
        self, mock_pinot, mock_kafka
    ):
        """El SRS pide indicar cual es el ticket existente "para que continue la
        conversacion ahi": decir solo que no se puede es un callejon sin salida."""
        # Arrange
        factura = _factura()
        datos = {
            "idcliente": 1,
            "asunto": "Cargo indebido",
            "descripcion": "Discrepancia en el excedente facturado",
            "tipo": "facturacion",
            "idfactura": factura["id_factura"],
        }
        primero = RegistrarTicketService().registrar(**datos)

        # Act
        with pytest.raises(ValueError) as exc:
            RegistrarTicketService().registrar(**datos)

        # Assert
        assert f"#{primero['id_reclamo']}" in str(exc.value)
