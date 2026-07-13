import pytest

from apps.accidentes.services.cobertura_operativa_service import CoberturaOperativaService


@pytest.mark.service
class TestCoberturaOperativaService:
    def test_en_cobertura_por_calle_when_in_production_returns_true(self, mock_pinot):
        # Arrange
        service = CoberturaOperativaService()

        # Act
        result = service.en_cobertura_por_calle(1)

        # Assert
        assert result is True
