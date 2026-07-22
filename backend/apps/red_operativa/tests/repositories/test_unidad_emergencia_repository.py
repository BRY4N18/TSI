import pytest

from core.repositories.red_operativa.unidad_emergencia_repository import (
    UnidadEmergenciaRepository,
)


@pytest.mark.repository
class TestUnidadEmergenciaRepository:
    def test_create_when_valid_publishes_to_kafka(self, mock_pinot, mock_kafka):
        # Arrange
        repo = UnidadEmergenciaRepository()
        data = {
            "idcliente": 1,
            "idcondado": 1,
            "tipopropiedad": "Externa",
            "placa": "NEW-001",
            "contactoproveedor": "5551234",
            "unidademergencia": "Ambulancia Norte",
            "tipounidademergencia": "Ambulancia",
        }

        # Act
        result = repo.create(data)

        # Assert
        assert result["placa"] == "NEW-001"
        assert result["activo"] is True
        assert len(mock_kafka) == 1

    def test_find_by_placa_activa_when_exists_returns_unidad(
        self, mock_pinot, mock_kafka, mock_unidad_emergencia
    ):
        # Arrange
        repo = UnidadEmergenciaRepository()

        # Act
        result = repo.find_by_placa_activa(mock_unidad_emergencia["placa"])

        # Assert
        assert result is not None
        assert result["idunidademergencia"] == mock_unidad_emergencia["idunidademergencia"]

    def test_find_by_placa_activa_when_not_exists_returns_none(self, mock_pinot, mock_kafka):
        # Arrange
        repo = UnidadEmergenciaRepository()

        # Act
        result = repo.find_by_placa_activa("NO-EXISTE")

        # Assert
        assert result is None

    def test_condado_exists_when_valid_returns_true(self, mock_pinot, mock_kafka):
        # Arrange
        repo = UnidadEmergenciaRepository()

        # Act
        result = repo.condado_exists(1)

        # Assert
        assert result is True

    def test_condado_exists_when_invalid_returns_false(self, mock_pinot, mock_kafka):
        # Arrange
        repo = UnidadEmergenciaRepository()

        # Act
        result = repo.condado_exists(999999)

        # Assert
        assert result is False

    def test_update_when_valid_publishes_to_kafka(
        self, mock_pinot, mock_kafka, mock_unidad_emergencia
    ):
        # Arrange
        repo = UnidadEmergenciaRepository()

        # Act
        updated = repo.update(
            mock_unidad_emergencia["idunidademergencia"], {"capacidad": "6"}
        )

        # Assert
        assert updated is not None
        assert updated["capacidad"] == "6"
        assert len(mock_kafka) == 1
