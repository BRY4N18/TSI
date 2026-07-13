import pytest

from apps.accidentes.services.geocodificacion_inversa_service import GeocodificacionInversaService


@pytest.mark.service
class TestGeocodificacionInversaService:
    def test_sugerir_when_coords_valid_returns_calle(self, mock_pinot):
        # Arrange
        service = GeocodificacionInversaService()

        # Act
        result = service.sugerir(19.43, -99.13)

        # Assert
        assert result["idcalle"] == 1
        assert result["en_cobertura_operativa"] is True
