import time

import pytest

from apps.despacho.services.timeout_despacho_service import TimeoutDespachoService
from core.repositories.despacho.despacho_repository import DespachoRepository
from core.repositories.despacho.historial_despacho_repository import (
    ESTADO_PENDIENTE,
    HistorialDespachoRepository,
)
from core.repositories.despacho.notificacion_despacho_repository import NotificacionDespachoRepository


@pytest.mark.service
class TestTimeoutDespachoService:
    def test_procesar_ciclo_when_expired_marks_timeout_and_publishes_event(
        self, mock_pinot, mock_kafka, accidente_activo
    ):
        # Arrange
        old_ts = int(time.time() * 1000) - 120_000
        notif = NotificacionDespachoRepository().publish_create(
            {"idaccidente": accidente_activo, "idunidaddemergencia": 1}
        )
        desp = DespachoRepository().publish_create(
            {
                "idaccidente": accidente_activo,
                "idunidademergencia": 1,
                "idnotificaciondespacho": notif["idnotificaciondespacho"],
                "idorigendespacho": "Automatico",
                "fechahoradespacho": old_ts,
            }
        )
        HistorialDespachoRepository().publish(
            iddespacho=desp["iddespacho"], estadonuevo=ESTADO_PENDIENTE
        )
        svc = TimeoutDespachoService()

        # Act
        eventos = svc.procesar_ciclo()

        # Assert
        assert len(eventos) == 1
        assert eventos[0]["iddespacho"] == desp["iddespacho"]
        updated = DespachoRepository().find_by_id(desp["iddespacho"])
        assert updated["activo"] is False

    def test_procesar_ciclo_when_recent_skips(self, mock_pinot, mock_kafka, despacho_pendiente_unidad):
        # Arrange
        svc = TimeoutDespachoService()

        # Act
        eventos = svc.procesar_ciclo()

        # Assert
        assert eventos == []
