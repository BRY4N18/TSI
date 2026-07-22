import pytest

from apps.despacho.services.asignacion_inteligente_service import (
    AsignacionInteligenteService,
)


@pytest.mark.service
class TestAsignacionInteligenteService:
    def test_ejecutar_when_candidata_creates_despacho_and_notifica(
        self, mock_pinot, mock_kafka, accidente_activo, unidad_con_estado_activa
    ):
        # Arrange
        svc = AsignacionInteligenteService()

        # Act
        result = svc.ejecutar(idaccidente=accidente_activo, idusuario=2)

        # Assert
        assert result is not None
        assert result["iddespacho"] is not None
        assert result["idnotificaciondespacho"] is not None
        assert result["entrega"]["estado"] in ("Notificada", "No_entregada")

    def test_ejecutar_when_no_candidatas_returns_none(
        self, mock_pinot, mock_kafka, accidente_activo
    ):
        # Arrange
        svc = AsignacionInteligenteService()

        # Act
        result = svc.ejecutar(idaccidente=accidente_activo)

        # Assert
        assert result is None
