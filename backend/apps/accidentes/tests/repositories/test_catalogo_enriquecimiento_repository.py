import pytest

from core.repositories.evidencia.catalogo_enriquecimiento_repository import (
    CatalogoEnriquecimientoRepository,
)


@pytest.mark.repository
class TestCatalogoEnriquecimientoRepository:
    def test_list_periodos_when_seeded_returns_activos(self, mock_pinot, mock_kafka):
        # Arrange
        repo = CatalogoEnriquecimientoRepository()

        # Act
        rows = repo.list_periodos_dias()

        # Assert
        assert len(rows) >= 1
        assert rows[0]["idperiododia"] == 1

    def test_find_estado_conductor_when_valid_returns_row(self, mock_pinot, mock_kafka):
        # Arrange
        repo = CatalogoEnriquecimientoRepository()

        # Act
        row = repo.find_estado_conductor(1)

        # Assert
        assert row is not None
        assert row["condicionfisica"] is True

    def test_find_elemento_fisico_when_invalid_returns_none(self, mock_pinot, mock_kafka):
        # Arrange
        repo = CatalogoEnriquecimientoRepository()

        # Act / Assert
        assert repo.find_elemento_fisico(999) is None
