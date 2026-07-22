import time

import pytest

from apps.despacho.consumers.despacho_timeout_consumer import DespachoTimeoutConsumer
from apps.despacho.jobs.timeout_despacho_job import run_timeout_despacho_job
from apps.despacho.services.timeout_despacho_service import TimeoutDespachoService
from core.repositories.despacho.despacho_repository import DespachoRepository
from core.repositories.despacho.historial_despacho_repository import (
    ESTADO_PENDIENTE,
    HistorialDespachoRepository,
)
from core.repositories.despacho.notificacion_despacho_repository import (
    NotificacionDespachoRepository,
)


@pytest.mark.critical_path
class TestTimeoutReasignacionIntegration:
    def test_o35_job_publishes_event_and_o36_reassigns(
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

        # Act
        eventos = run_timeout_despacho_job()
        consumer_result = DespachoTimeoutConsumer().handle(eventos[0])

        # Assert
        assert len(eventos) == 1
        assert consumer_result["reasignacion_iniciada"] is True
        despachos = DespachoRepository().list_by_accidente(accidente_activo)
        assert len(despachos) >= 2
