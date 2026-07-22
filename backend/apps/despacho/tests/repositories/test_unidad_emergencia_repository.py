import pytest

from core.repositories.despacho.unidad_emergencia_repository import (
    UnidadEmergenciaRepository,
)


@pytest.mark.repository
class TestUnidadEmergenciaRepository:
    def test_find_by_usuario_when_linked_returns_unit(self, mock_pinot, mock_kafka):
        # Arrange
        repo = UnidadEmergenciaRepository()

        # Act
        unit = repo.find_by_usuario(6)

        # Assert
        assert unit is not None
        assert unit["idunidademergencia"] == 1

    def test_list_active_returns_active_units(self, mock_pinot, mock_kafka):
        # Arrange
        repo = UnidadEmergenciaRepository()

        # Act
        units = repo.list_active()

        # Assert
        assert len(units) >= 2
        assert all(u.get("activo") for u in units)
