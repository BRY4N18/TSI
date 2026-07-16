from unittest.mock import patch

import pytest

from apps.seguimiento.services.ruta_service import RutaCoordenadasInvalidasError, RutaService
from core.osrm.client import OsrmError


@pytest.mark.service
class TestRutaService:
    def test_obtener_ruta_when_osrm_ok_returns_puntos(self):
        # Arrange
        svc = RutaService()
        with patch(
            "apps.seguimiento.services.ruta_service.OsrmClient.route",
            return_value=[(4.65, -74.08), (4.60, -74.07)],
        ):
            # Act
            result = svc.obtener_ruta("4.65,-74.08", "4.60,-74.07")

        # Assert
        assert result == {
            "puntos": [
                {"latitud": 4.65, "longitud": -74.08},
                {"latitud": 4.60, "longitud": -74.07},
            ]
        }

    def test_obtener_ruta_when_osrm_falla_returns_puntos_vacio(self):
        # Arrange
        svc = RutaService()
        with patch(
            "apps.seguimiento.services.ruta_service.OsrmClient.route",
            side_effect=OsrmError("timeout"),
        ):
            # Act
            result = svc.obtener_ruta("4.65,-74.08", "4.60,-74.07")

        # Assert
        assert result == {"puntos": []}

    def test_obtener_ruta_when_formato_invalido_raises(self):
        # Arrange
        svc = RutaService()

        # Act / Assert
        with pytest.raises(RutaCoordenadasInvalidasError):
            svc.obtener_ruta("no-es-coordenada", "4.60,-74.07")
