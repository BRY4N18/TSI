import pytest

from core.repositories.despacho.geografia_repository import GeografiaRepository


@pytest.mark.repository
class TestGeografiaRepository:
    def test_resolve_condado_from_idcalle_when_valid_returns_condado(self, mock_pinot, mock_kafka):
        # Arrange
        repo = GeografiaRepository()

        # Act
        idcondado = repo.resolve_condado_from_idcalle(1)

        # Assert
        assert idcondado == 1

    def test_list_condados_vecinos_when_configured_returns_neighbors(self, mock_pinot, mock_kafka):
        # Arrange
        repo = GeografiaRepository()

        # Act
        vecinos = repo.list_condados_vecinos(1)

        # Assert
        assert vecinos == [2]
