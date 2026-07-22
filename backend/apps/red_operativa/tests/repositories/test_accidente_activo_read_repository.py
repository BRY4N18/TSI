import pytest

from core.repositories.red_operativa.accidente_activo_read_repository import (
    AccidenteActivoReadRepository,
)


@pytest.mark.repository
class TestAccidenteActivoReadRepository:
    def test_existen_casos_activos_when_con_casos_returns_true(
        self, mock_pinot, mock_kafka, pinot_store
    ):
        # Arrange
        pinot_store["Fact_Accidente"].append(
            {"idaccidente": "acc-1", "idcalle": 1, "activo": True}
        )
        repo = AccidenteActivoReadRepository()

        # Act
        result = repo.existen_casos_activos(1)

        # Assert
        assert result is True

    def test_existen_casos_activos_when_sin_casos_returns_false(
        self, mock_pinot, mock_kafka, pinot_store
    ):
        # Arrange
        repo = AccidenteActivoReadRepository()

        # Act
        result = repo.existen_casos_activos(1)

        # Assert
        assert result is False

    def test_existen_casos_activos_when_casos_cerrados_returns_false(
        self, mock_pinot, mock_kafka, pinot_store
    ):
        # Arrange
        pinot_store["Fact_Accidente"].append(
            {"idaccidente": "acc-2", "idcalle": 1, "activo": False}
        )
        repo = AccidenteActivoReadRepository()

        # Act
        result = repo.existen_casos_activos(1)

        # Assert
        assert result is False

    def test_existen_casos_activos_when_region_sin_cobertura_geografica_returns_false(
        self, mock_pinot, mock_kafka, pinot_store
    ):
        # Arrange
        repo = AccidenteActivoReadRepository()

        # Act
        result = repo.existen_casos_activos(999)

        # Assert
        assert result is False
