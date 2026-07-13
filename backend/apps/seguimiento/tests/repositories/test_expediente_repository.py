import pytest

from core.repositories.seguimiento.expediente_repository import ExpedienteRepository


@pytest.mark.repository
class TestExpedienteRepository:
    def test_find_accidente_when_exists_returns_row(self, mock_pinot, mock_kafka, accidente_activo):
        # Arrange
        repo = ExpedienteRepository()

        # Act
        row = repo.find_accidente(accidente_activo)

        # Assert
        assert row is not None
        assert row["idaccidente"] == accidente_activo

    def test_find_accidente_when_missing_returns_none(self, mock_pinot, mock_kafka):
        # Arrange
        repo = ExpedienteRepository()

        # Act
        row = repo.find_accidente("ACC-MISSING")

        # Assert
        assert row is None
