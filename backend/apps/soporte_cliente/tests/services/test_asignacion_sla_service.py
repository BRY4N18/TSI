import pytest

from apps.soporte_cliente.services.asignacion_sla_service import AsignacionSLAService


@pytest.mark.service
class TestAsignacionSLAService:
    def test_asignar_when_regla_vigente_returns_sla_fields(self, mock_pinot, mock_kafka):
        # Arrange
        service = AsignacionSLAService()

        # Act
        resultado = service.asignar(idcliente=1, tipo_incidencia="tecnica", prioridad="alta")

        # Assert
        assert resultado is not None
        assert resultado["idslaconfig"] == 1
        assert resultado["sla_status"] == "en curso"
        assert resultado["sla_resolucion"] > resultado["sla_primera_respuesta"]

    def test_asignar_when_sin_suscripcion_activa_returns_none(self, mock_pinot, mock_kafka):
        # Arrange
        service = AsignacionSLAService()

        # Act
        resultado = service.asignar(idcliente=999, tipo_incidencia="tecnica", prioridad="alta")

        # Assert
        assert resultado is None

    def test_asignar_when_sin_regla_coincidente_returns_none(self, mock_pinot, mock_kafka):
        # Arrange
        service = AsignacionSLAService()

        # Act
        resultado = service.asignar(idcliente=1, tipo_incidencia="inexistente", prioridad="baja")

        # Assert
        assert resultado is None


@pytest.mark.service
class TestTicketClasificadoSinReglaAplicable:
    """B43 — un ticket YA clasificado para el que no hay compromiso aplicable
    quedaba con `sla_status=None`, igual que uno sin clasificar. La diferencia es
    enorme: el sin clasificar tiene su propio estado y salta a la vista, y este se
    presentaba como un ticket normal que **nadie estaba cronometrando**."""

    def test_sin_suscripcion_activa_el_ticket_lo_dice(self, mock_pinot, mock_kafka):
        # Arrange — sin suscripcion activa no hay plan, y sin plan no hay regla
        from apps.soporte_cliente.services.registrar_ticket_service import (
            RegistrarTicketService,
        )

        # Act
        reclamo = RegistrarTicketService().registrar(
            idcliente=99_999,  # cliente sin suscripcion
            asunto="La API no responde",
            descripcion="Recibo error 500 de forma constante",
            tipo="tecnico",
        )

        # Assert
        assert reclamo["estado"] == "Abierto"  # esta clasificado
        assert reclamo["tipo_incidencia"] is not None
        assert reclamo["sla_status"] == "sin compromiso"
        assert reclamo["idslaconfig"] is None

    def test_el_vigilante_no_lo_confunde_con_uno_cronometrado(
        self, mock_pinot, mock_kafka
    ):
        # Arrange
        from apps.soporte_cliente.services.monitoreo_sla_service import (
            MonitoreoSLAService,
        )
        from apps.soporte_cliente.services.registrar_ticket_service import (
            RegistrarTicketService,
        )

        RegistrarTicketService().registrar(
            idcliente=99_999,
            asunto="La API no responde",
            descripcion="Recibo error 500 de forma constante",
            tipo="tecnico",
        )

        # Act — no debe marcarlo en riesgo ni escalarlo: no hay plazo que cruzar
        resultado = MonitoreoSLAService().ejecutar_ciclo()

        # Assert
        assert resultado["escalados"] == 0
        assert resultado["en_riesgo"] == 0
