import pytest

from core.repositories.accidentes.region_operativa_repository import RegionOperativaRepository


@pytest.mark.repository
class TestRegionOperativaRepository:
    def test_resolve_estado_from_calle_when_exists_returns_id(self, mock_pinot):
        # Arrange
        repo = RegionOperativaRepository()

        # Act
        idestado = repo.resolve_estado_from_calle(1)

        # Assert
        assert idestado == 1

    def test_is_estado_en_produccion_when_covered_returns_true(self, mock_pinot):
        # Arrange
        repo = RegionOperativaRepository()

        # Act
        result = repo.is_estado_en_produccion(1)

        # Assert
        assert result is True
