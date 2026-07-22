import pytest

from conftest import PINOT_STORE
from core.repositories.despacho.ubicacion_unidad_repository import (
    UbicacionUnidadRepository,
)


@pytest.mark.repository
class TestUbicacionUnidadRepository:
    def test_posicion_efectiva_when_no_gps_returns_snapshot(self, mock_pinot, mock_kafka):
        # Arrange
        repo = UbicacionUnidadRepository()

        # Act
        pos = repo.posicion_efectiva(1)

        # Assert
        assert pos == {"latitud": 19.43, "longitud": -99.13}

    def test_posicion_efectiva_when_gps_more_recent_returns_gps(self, mock_pinot, mock_kafka):
        # Arrange
        PINOT_STORE["Dim_HistorialUbicacionUnidadEmergencia"].append(
            {
                "idhistorialunidademergencia": 1,
                "idunidademergencia": 1,
                "idaccidente": "ACC-GPS",
                "latitud": 19.50,
                "longitud": -99.20,
                "fechahora": 1804067200000,
            }
        )
        repo = UbicacionUnidadRepository()

        # Act
        pos = repo.posicion_efectiva(1)

        # Assert
        assert pos == {"latitud": 19.50, "longitud": -99.20}
