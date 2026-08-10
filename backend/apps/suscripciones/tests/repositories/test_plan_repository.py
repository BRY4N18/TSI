import pytest

from core.repositories.suscripciones.plan_repository import PlanRepository

pytestmark = pytest.mark.repository


class TestPlanRepository:
    def test_list_solo_activos_paginado(self, mock_pinot, mock_kafka):
        # Arrange
        from unittest.mock import patch

        from core.pinot.client import PinotClient

        repo = PlanRepository()
        captured: list[str] = []

        def capture(sql, params=None):
            captured.append(sql)
            return mock_pinot(sql, params)

        # Act
        with patch.object(PinotClient, "query", side_effect=capture):
            rows, next_cursor = repo.list(solo_activos=True, limit=20)
        # Assert
        assert all(r["activo"] for r in rows)
        assert len(rows) == 3
        assert next_cursor is None
        assert any("LIMIT" in s.upper() for s in captured)
        assert all("SELECT * FROM Dim_Plan WHERE" not in s.replace("\n", " ") or "idplan >" in s.lower() for s in captured)
        assert any("idplan >" in s.lower() for s in captured)

    def test_list_respects_limit_and_next_cursor(self, mock_pinot, mock_kafka, pinot_store):
        repo = PlanRepository()
        for i in range(5, 12):
            pinot_store["Dim_Plan"].append(
                {
                    "idplan": i,
                    "nombre": f"Plan {i}",
                    "nivel": "Básico",
                    "limites": '{"unidades_max": 1, "usuarios_max": 1, "api_calls_mes": 1, "api_calls_minuto": 1}',
                    "activo": True,
                    "precio": 10.0,
                    "fecha_actualizacion": "2026-01-01T00:00:00+00:00",
                }
            )

        page1, next1 = repo.list(activo=True, limit=3, cursor=0)
        assert len(page1) == 3
        assert next1 == page1[-1]["idplan"]

        page2, _next2 = repo.list(activo=True, limit=3, cursor=next1)
        ids1 = {r["idplan"] for r in page1}
        ids2 = {r["idplan"] for r in page2}
        assert ids1.isdisjoint(ids2)
        assert all(i > next1 for i in ids2)

    def test_list_filters_q_activo_nivel(self, mock_pinot, mock_kafka):
        repo = PlanRepository()
        rows, _ = repo.list(q="profes", activo=True, limit=20)
        assert len(rows) == 1
        assert rows[0]["nombre"] == "Profesional"

        inactivos, _ = repo.list(activo=False, limit=20)
        assert len(inactivos) == 1
        assert inactivos[0]["idplan"] == 4

        nivel, _ = repo.list(nivel="Empresarial", activo=True, limit=20)
        assert len(nivel) == 1
        assert nivel[0]["nivel"] == "Empresarial"

    def test_create_publishes_kafka(self, mock_pinot, mock_kafka):
        # Arrange
        repo = PlanRepository()
        # Act
        plan = repo.create(
            {
                "nombre": "Plus",
                "precio": 79.0,
                "nivel": "Básico",
                "limites": {"unidades_max": 8, "usuarios_max": 4, "api_calls_mes": 2000, "api_calls_minuto": 60},
            }
        )
        # Assert
        assert plan["idplan"] == 5
        assert mock_kafka[-1]["topic"].endswith("Dim_Plan_topic")
        assert repo.find_by_id(5)["nombre"] == "Plus"
