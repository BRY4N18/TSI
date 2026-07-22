import pytest

from apps.despacho.services.asignacion_inteligente_service import (
    AsignacionInteligenteService,
)
from apps.despacho.services.confirmar_despacho_service import ConfirmarDespachoService
from core.repositories.despacho.notificacion_despacho_repository import (
    ESTADO_CONFIRMADA,
    NotificacionDespachoRepository,
)


@pytest.mark.service
class TestConfirmarDespachoService:
    def test_confirmar_when_pendiente_marks_confirmada_and_ocupada(
        self, mock_pinot, mock_kafka, accidente_activo, unidad_con_estado_activa
    ):
        # Arrange
        created = AsignacionInteligenteService().ejecutar(
            idaccidente=accidente_activo, idusuario=2
        )
        assert created is not None
        svc = ConfirmarDespachoService()

        # Act
        result = svc.confirmar(
            idnotificaciondespacho=created["idnotificaciondespacho"],
            idunidademergencia=1,
            idusuario=6,
        )

        # Assert
        assert result["estado_unidad"] == "En Misión"
        assert result["estado_caso"] == "ASIGNADO"
        assert result["idunidademergencia"] == 1
        notif = NotificacionDespachoRepository().find_by_id(created["idnotificaciondespacho"])
        assert notif["estadonotificaciondespacho"] == ESTADO_CONFIRMADA
