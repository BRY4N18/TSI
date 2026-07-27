import pytest

from core.repositories.ventas_crm.interaccion_demo_repository import InteraccionDemoRepository

pytestmark = pytest.mark.repository


def test_interaccion_demo_create_and_list(mock_pinot, mock_kafka):
    # Arrange
    repo = InteraccionDemoRepository()
    # Act
    row = repo.create(
        {
            "idprospecto": 10,
            "tipo_evento": "click",
            "seccion": "precios",
            "metadata": "{}",
            "timestamp_evento": 1_000,
        }
    )
    listed = repo.list_by_prospecto(10)
    # Assert
    assert row["idinteraccion"] >= 1
    assert any(r["idinteraccion"] == row["idinteraccion"] for r in listed)
    assert any(m["topic"].endswith("Fact_Interaccion_Demo_topic") for m in mock_kafka)
