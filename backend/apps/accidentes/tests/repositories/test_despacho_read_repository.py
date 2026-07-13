import pytest

from core.repositories.accidentes.despacho_read_repository import DespachoReadRepository


@pytest.mark.repository
class TestDespachoReadRepository:
    def test_has_active_confirmed_when_despacho_exists_returns_true(self, mock_pinot, pinot_store):
        # Arrange
        pinot_store["Fact_Despacho"].append(
            {"iddespacho": 1, "idaccidente": "ACC-DESP", "activo": True}
        )
        repo = DespachoReadRepository()

        # Act
        result = repo.has_active_confirmed("ACC-DESP")

        # Assert
        assert result is True

    def test_has_active_confirmed_when_missing_returns_false(self, mock_pinot):
        # Arrange
        repo = DespachoReadRepository()

        # Act
        result = repo.has_active_confirmed("ACC-NONE")

        # Assert
        assert result is False
