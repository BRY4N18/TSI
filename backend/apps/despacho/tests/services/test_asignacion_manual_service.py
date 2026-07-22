import pytest

from apps.despacho.services.asignacion_inteligente_service import (
    AsignacionInteligenteService,
)
from apps.despacho.services.asignacion_manual_service import AsignacionManualService
from apps.despacho.services.coordinacion_multiple_service import (
    CoordinacionMultipleService,
)
from apps.despacho.services.escalamiento_zona_service import EscalamientoZonaService
from apps.despacho.services.monitoreo_despacho_service import MonitoreoDespachoService


@pytest.mark.service
class TestAsignacionManualService:
    def test_asignar_when_valid_creates_manual_despacho(
        self, mock_pinot, mock_kafka, accidente_activo, unidad_con_estado_activa
    ):
        # Arrange
        svc = AsignacionManualService()

        # Act
        result = svc.asignar(idaccidente=accidente_activo, idunidademergencia=1, idusuario=2)

        # Assert
        assert result["origen"] == "Manual"
        assert result["iddespacho"] is not None


@pytest.mark.service
class TestEscalamientoZonaService:
    def test_escalar_when_vecino_available_dispatches(
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
        svc = EscalamientoZonaService()

        # Act
        result = svc.escalar(idaccidente=accidente_activo, idusuario=2)

        # Assert
        assert result.get("iddespacho") or result.get("alerta_registrada") is not None


@pytest.mark.service
class TestCoordinacionMultipleService:
    def test_coordinar_when_active_exists_adds_second_unit(
        self, mock_pinot, mock_kafka, accidente_activo, unidad_con_estado_activa, despacho_pendiente_unidad
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
        svc = CoordinacionMultipleService()

        # Act
        result = svc.coordinar(idaccidente=accidente_activo, idunidademergencia=2, idusuario=2)

        # Assert
        assert result["iddespacho"] is not None


@pytest.mark.service
class TestMonitoreoDespachoService:
    def test_obtener_estado_when_despachos_exist_returns_intentos(
        self, mock_pinot, mock_kafka, accidente_activo, despacho_pendiente_unidad
    ):
        # Arrange
        svc = MonitoreoDespachoService()

        # Act
        estado = svc.obtener_estado(accidente_activo)

        # Assert
        assert estado["idaccidente"] == accidente_activo
        assert len(estado["intentos"]) >= 1
