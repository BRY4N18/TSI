import pytest

from core.repositories.red_operativa.despacho_activo_read_repository import (
    DespachoActivoReadRepository,
)


@pytest.mark.repository
class TestDespachoActivoReadRepository:
    def test_has_despacho_activo_when_exists_returns_true(
        self, mock_pinot, mock_kafka, mock_despacho_activo
    ):
        # Arrange
        repo = DespachoActivoReadRepository()

        # Act
        result = repo.has_despacho_activo(mock_despacho_activo["idunidademergencia"])

        # Assert
        assert result is True

    def test_has_despacho_activo_when_not_exists_returns_false(
        self, mock_pinot, mock_kafka, mock_unidad_emergencia
    ):
        # Arrange
        repo = DespachoActivoReadRepository()

        # Act
        result = repo.has_despacho_activo(mock_unidad_emergencia["idunidademergencia"])

        # Assert
        assert result is False
