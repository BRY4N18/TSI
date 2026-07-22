import pytest

from core.repositories.red_operativa.baja_unidad_repository import BajaUnidadRepository


@pytest.mark.repository
class TestBajaUnidadRepository:
    def test_create_when_valid_publishes_to_kafka(self, mock_pinot, mock_kafka, mock_unidad_emergencia):
        # Arrange
        repo = BajaUnidadRepository()

        # Act
        result = repo.create(
            {
                "idunidademergencia": mock_unidad_emergencia["idunidademergencia"],
                "idusuario": 1,
                "motivo": "Fuera de servicio permanente",
                "tipobaja": "Normal",
            }
        )

        # Assert
        assert result["idunidademergencia"] == mock_unidad_emergencia["idunidademergencia"]
        assert result["tipobaja"] == "Normal"
        assert len(mock_kafka) == 1

    def test_list_by_unidad_when_exists_returns_rows(
        self, mock_pinot, mock_kafka, mock_unidad_emergencia
    ):
        # Arrange
        repo = BajaUnidadRepository()
        repo.create(
            {
                "idunidademergencia": mock_unidad_emergencia["idunidademergencia"],
                "idusuario": 1,
                "motivo": "Motivo test",
                "tipobaja": "Normal",
            }
        )

        # Act
        result = repo.list_by_unidad(mock_unidad_emergencia["idunidademergencia"])

        # Assert
        assert len(result) == 1

    def test_list_by_unidad_when_none_returns_empty(self, mock_pinot, mock_kafka):
        # Arrange
        repo = BajaUnidadRepository()

        # Act
        result = repo.list_by_unidad(999999)

        # Assert
        assert result == []
