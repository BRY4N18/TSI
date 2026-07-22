import pytest

from apps.seguimiento.services.registrar_posicion_gps_service import (
    RegistrarPosicionGpsService,
)
from core.repositories.seguimiento.historial_ubicacion_repository import (
    HistorialUbicacionRepository,
)


@pytest.mark.service
class TestRegistrarPosicionGpsService:
    def test_registrar_when_confirmado_persists_gps(
        self,
        mock_pinot,
        mock_kafka,
        accidente_activo,
        despacho_confirmado_unidad,
    ):
        # Arrange
        svc = RegistrarPosicionGpsService()

        # Act
        result = svc.registrar(
            idunidademergencia=1,
            idaccidente=accidente_activo,
            latitud=19.4326,
            longitud=-99.1332,
            fechahora=1_700_000_000_000,
            idusuario=6,
        )

        # Assert
        assert result["aceptado"] is True
        rows = HistorialUbicacionRepository().list_by_unidad(1)
        assert len(rows) >= 1

    def test_registrar_when_geofence_hysteresis_met_auto_llegada(
        self,
        mock_pinot,
        mock_kafka,
        accidente_activo,
        despacho_confirmado_unidad,
    ):
        # Arrange
        svc = RegistrarPosicionGpsService()
        base = 1_700_000_000_000

        # Act
        first = svc.registrar(
            idunidademergencia=1,
            idaccidente=accidente_activo,
            latitud=19.4326,
            longitud=-99.1332,
            fechahora=base,
            idusuario=6,
        )
        second = svc.registrar(
            idunidademergencia=1,
            idaccidente=accidente_activo,
            latitud=19.4326,
            longitud=-99.1332,
            fechahora=base + 31_000,
            idusuario=6,
        )

        # Assert
        assert first["llegada_automatica"] is False
        assert second["llegada_automatica"] is True
