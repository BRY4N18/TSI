import pytest

from core.repositories.red_operativa.validacion_region_repository import (
    ValidacionRegionRepository,
)


@pytest.mark.repository
class TestValidacionRegionRepository:
    def test_create_never_overwrites_previous_row(self, mock_pinot, mock_kafka):
        # Arrange
        repo = ValidacionRegionRepository()
        repo.create({"idregionoperativa": 1, "idusuario": 1, "resultado": "Rechazada", "motivo": "x"})

        # Act
        repo.create({"idregionoperativa": 1, "idusuario": 9, "resultado": "Aprobada"})

        # Assert
        historial = repo.list_by_region(1)
        assert len(historial) == 2
        assert historial[0]["resultado"] == "Rechazada"
        assert historial[1]["resultado"] == "Aprobada"

    def test_list_by_region_when_multiple_rows_orders_by_fechahora(self, mock_pinot, mock_kafka):
        # Arrange
        repo = ValidacionRegionRepository()
        repo.create(
            {
                "idregionoperativa": 1,
                "idusuario": 1,
                "resultado": "Rechazada",
                "motivo": "a",
                "fechahora": "2026-01-01T00:00:00+00:00",
            }
        )
        repo.create(
            {
                "idregionoperativa": 1,
                "idusuario": 1,
                "resultado": "Aprobada",
                "fechahora": "2026-01-02T00:00:00+00:00",
            }
        )

        # Act
        historial = repo.list_by_region(1)

        # Assert
        assert [h["fechahora"] for h in historial] == [
            "2026-01-01T00:00:00+00:00",
            "2026-01-02T00:00:00+00:00",
        ]

    def test_existe_aprobada_when_true(self, mock_pinot, mock_kafka):
        # Arrange
        repo = ValidacionRegionRepository()
        repo.create({"idregionoperativa": 1, "idusuario": 9, "resultado": "Aprobada"})

        # Act & Assert
        assert repo.existe_aprobada(1) is True

    def test_existe_aprobada_when_false(self, mock_pinot, mock_kafka):
        # Arrange
        repo = ValidacionRegionRepository()
        repo.create({"idregionoperativa": 1, "idusuario": 1, "resultado": "Rechazada", "motivo": "x"})

        # Act & Assert
        assert repo.existe_aprobada(1) is False
