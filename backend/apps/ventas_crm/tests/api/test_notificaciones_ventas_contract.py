import pytest

from core.repositories.ventas_crm.notificacion_ventas_repository import (
    NotificacionVentasRepository,
)

pytestmark = pytest.mark.api


def test_notificaciones_gerente(api_client, gerente_ventas_auth_headers, mock_kafka):
    # Arrange
    NotificacionVentasRepository().create(
        {
            "id_prospecto": 1,
            "idinteraccion": 1,
            "idusuariogerentenotificado": 20,
            "regladisparada": "visito_pricing_3x",
            "canal": "push",
        }
    )
    # Act
    r = api_client.get("/api/v1/ventas-crm/notificaciones", **gerente_ventas_auth_headers)
    # Assert
    assert r.status_code == 200
    assert all(x["idusuariogerentenotificado"] == 20 for x in r.data["data"])
