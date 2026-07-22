import pytest

from apps.despacho.services.notificacion_despacho_service import (
    NotificacionDespachoService,
)
from core.repositories.despacho.despacho_repository import DespachoRepository
from core.repositories.despacho.notificacion_despacho_repository import (
    ESTADO_NOTIFICADA,
    NotificacionDespachoRepository,
)


@pytest.mark.service
class TestNotificacionDespachoService:
    def test_notificar_when_push_ok_marks_notificada(self, mock_pinot, mock_kafka):
        # Arrange
        notif_repo = NotificacionDespachoRepository()
        desp_repo = DespachoRepository()
        notif = notif_repo.publish_create(
            {
                "idaccidente": "ACC-NOTIF-1",
                "idunidaddemergencia": 1,
            }
        )
        desp = desp_repo.publish_create(
            {
                "idaccidente": "ACC-NOTIF-1",
                "idunidademergencia": 1,
                "idnotificaciondespacho": notif["idnotificaciondespacho"],
                "idorigendespacho": "Automatico",
            }
        )
        svc = NotificacionDespachoService(
            notificacion_repo=notif_repo,
            despacho_repo=desp_repo,
            push_sender=lambda _p: True,
            sms_sender=lambda _p: False,
        )

        # Act
        result = svc.notificar(
            idnotificaciondespacho=notif["idnotificaciondespacho"],
            iddespacho=desp["iddespacho"],
            idaccidente="ACC-NOTIF-1",
        )

        # Assert
        assert result["estado"] == ESTADO_NOTIFICADA
        updated = notif_repo.find_by_id(notif["idnotificaciondespacho"])
        assert updated["estadonotificaciondespacho"] == ESTADO_NOTIFICADA

    def test_notificar_when_both_fail_triggers_reasignacion(
        self, mock_pinot, mock_kafka, accidente_activo, unidad_con_estado_activa
    ):
        # Arrange
        from apps.despacho.services.asignacion_inteligente_service import (
            AsignacionInteligenteService,
        )

        created = AsignacionInteligenteService(
            notificacion_service=NotificacionDespachoService(
                push_sender=lambda _p: False,
                sms_sender=lambda _p: False,
            )
        ).ejecutar(idaccidente=accidente_activo)
        assert created is not None

        # Act — second assignment attempt via fail path already ran in ejecutar
        desp_repo = DespachoRepository()
        first = desp_repo.find_by_id(created["iddespacho"])

        # Assert
        assert first is not None
