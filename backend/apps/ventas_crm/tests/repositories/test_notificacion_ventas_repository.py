import pytest

from core.repositories.ventas_crm.notificacion_ventas_repository import (
    NotificacionVentasRepository,
)

pytestmark = pytest.mark.repository


def test_notificacion_create_publish_and_dedup(mock_pinot, mock_kafka):
    # Arrange
    repo = NotificacionVentasRepository()
    # Act
    row = repo.create(
        {
            "id_prospecto": 5,
            "idinteraccion": 9,
            "idusuariogerentenotificado": 20,
            "regladisparada": "visito_pricing_3x",
            "canal": "email",
            "fechahoranotificacion": 1_720_000_000_000,
        }
    )
    exists = repo.exists_dedup_dia_utc(
        id_prospecto=5,
        regladisparada="visito_pricing_3x",
        day_start_ms=1_720_000_000_000,
        day_end_ms=1_720_086_400_000,
    )
    # Assert
    assert row["idnotificacion"] >= 1
    assert exists is True
    assert any(m["topic"].endswith("Fact_NotificacionVentas_topic") for m in mock_kafka)
