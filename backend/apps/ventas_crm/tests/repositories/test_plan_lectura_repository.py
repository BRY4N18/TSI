import pytest

from core.repositories.ventas_crm.plan_lectura_repository import PlanLecturaRepository


@pytest.mark.repository
def test_list_activos_excludes_inactive(mock_pinot, mock_kafka):
    # Arrange
    repo = PlanLecturaRepository()
    # Act
    rows = repo.list_activos()
    # Assert
    assert all(r.get("activo") is True for r in rows)
    assert not any(r.get("idplan") == 4 for r in rows)
    assert {r["nivel"] for r in rows} >= {"Básico", "Profesional", "Empresarial"}
    assert not hasattr(repo, "create")
    assert not hasattr(repo, "update")
    assert not hasattr(repo, "publish")
    assert not hasattr(repo, "kafka")
