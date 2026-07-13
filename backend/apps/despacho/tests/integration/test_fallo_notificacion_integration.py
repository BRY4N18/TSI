import pytest

from apps.despacho.services.asignacion_inteligente_service import AsignacionInteligenteService
from apps.despacho.services.notificacion_despacho_service import NotificacionDespachoService
from core.repositories.despacho.despacho_repository import DespachoRepository


@pytest.mark.critical_path
class TestFalloNotificacionIntegration:
    def test_o23_fail_triggers_o36_immediately(
        self, mock_pinot, mock_kafka, accidente_activo, unidad_con_estado_activa
    ):
        # Arrange
        from core.repositories.despacho.historial_estado_unidad_repository import (
            HistorialEstadoUnidadRepository,
        )

        HistorialEstadoUnidadRepository().append_estado(
            idunidademergencia=2,
            estadonuevo="Activa",
            idusuario=99,
            estadoanterior="Fuera de servicio",
        )
        svc = AsignacionInteligenteService(
            notificacion_service=NotificacionDespachoService(
                push_sender=lambda _p: False,
                sms_sender=lambda _p: False,
            )
        )

        # Act
        first = svc.ejecutar(idaccidente=accidente_activo, idusuario=2)

        # Assert
        assert first is not None
        despachos = DespachoRepository().list_by_accidente(accidente_activo)
        assert len(despachos) >= 2
