import pytest

from core.repositories.despacho.unidad_emergencia_repository import (
    UnidadEmergenciaRepository,
)


@pytest.mark.repository
class TestUnidadEmergenciaCandidatasRepository:
    def test_list_candidatas_por_condado_when_match_returns_units(self, mock_pinot, mock_kafka):
        # Arrange
        repo = UnidadEmergenciaRepository()

        # Act
        candidatas = repo.list_candidatas_por_condado(1)

        # Assert
        assert len(candidatas) == 1
        assert candidatas[0]["idunidademergencia"] == 1

    def test_list_candidatas_por_condado_with_vecinos_includes_neighbor(
        self, mock_pinot, mock_kafka
    ):
        # Arrange
        repo = UnidadEmergenciaRepository()

        # Act
        candidatas = repo.list_candidatas_por_condado(1, idcondados_extra=[2])

        # Assert
        ids = {u["idunidademergencia"] for u in candidatas}
        assert ids == {1, 2}
