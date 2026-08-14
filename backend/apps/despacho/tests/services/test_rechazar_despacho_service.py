import pytest

from apps.despacho.services.asignacion_inteligente_service import (
    AsignacionInteligenteService,
)
from apps.despacho.services.rechazar_despacho_service import RechazarDespachoService
from core.repositories.despacho.despacho_repository import DespachoRepository
from core.repositories.despacho.notificacion_despacho_repository import (
    ESTADO_RECHAZADA,
    NotificacionDespachoRepository,
)


@pytest.mark.service
class TestRechazarDespachoService:
    def test_rechazar_when_pendiente_deactivates_and_reassigns(
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
        created = AsignacionInteligenteService().ejecutar(
            idaccidente=accidente_activo, idusuario=2
        )
        assert created is not None
        svc = RechazarDespachoService()

        # Act
        result = svc.rechazar(
            idnotificaciondespacho=created["idnotificaciondespacho"],
            idunidademergencia=1,
            motivo="No disponible",
            idusuario=6,
        )

        # Assert
        assert result["reasignacion_iniciada"] is True
        notif = NotificacionDespachoRepository().find_by_id(created["idnotificaciondespacho"])
        assert notif["estadonotificaciondespacho"] == ESTADO_RECHAZADA
        desp = DespachoRepository().find_by_id(created["iddespacho"])
        assert desp["activo"] is False

    def test_rechazar_despacho_vencido_explica_que_vencio(
        self, mock_pinot, mock_kafka, accidente_activo, unidad_con_estado_activa
    ):
        # Arrange — la notificación sigue existiendo tras el vencimiento; lo que
        # ya no está vigente es el despacho. Responder "no encontrada" mandaba a
        # la unidad a buscar un problema que no existe.
        from apps.despacho.services.timeout_despacho_service import (
            TimeoutDespachoService,
        )

        created = AsignacionInteligenteService().ejecutar(
            idaccidente=accidente_activo, idusuario=2
        )
        assert created is not None
        TimeoutDespachoService().marcar_timeout(iddespacho=created["iddespacho"])

        # Act / Assert — ValueError (conflicto 409), no LookupError (404)
        with pytest.raises(ValueError, match="venció"):
            RechazarDespachoService().rechazar(
                idnotificaciondespacho=created["idnotificaciondespacho"],
                idunidademergencia=1,
                motivo="Ya no puedo",
                idusuario=6,
            )
