import pytest

from core.repositories.suscripciones.plan_repository import PlanRepository

pytestmark = pytest.mark.repository


class TestPlanRepository:
    def test_list_solo_activos(self, mock_pinot, mock_kafka):
        # Arrange
        repo = PlanRepository()
        # Act
        rows = repo.list(solo_activos=True)
        # Assert
        assert all(r["activo"] for r in rows)
        assert len(rows) == 3

    def test_create_publishes_kafka(self, mock_pinot, mock_kafka):
        # Arrange
        repo = PlanRepository()
        # Act
        plan = repo.create(
            {
                "nombre": "Plus",
                "precio": 79.0,
                "nivel": "Básico",
                "limites": {"unidades_max": 8, "usuarios_max": 4, "api_calls_mes": 2000},
            }
        )
        # Assert
        assert plan["idplan"] == 5
        assert mock_kafka[-1]["topic"].endswith("Dim_Plan_topic")
        assert repo.find_by_id(5)["nombre"] == "Plus"
