import pytest

from apps.ventas_crm.services.consulta_notificacion_ventas_service import (
    ConsultaNotificacionVentasService,
)
from core.repositories.ventas_crm.notificacion_ventas_repository import (
    NotificacionVentasRepository,
)

pytestmark = pytest.mark.service


def test_consulta_gerente_filtra(mock_pinot, mock_kafka):
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
    NotificacionVentasRepository().create(
        {
            "id_prospecto": 2,
            "idinteraccion": 2,
            "idusuariogerentenotificado": 21,
            "regladisparada": "visito_pricing_3x",
            "canal": "push",
        }
    )
    # Act
    rows = ConsultaNotificacionVentasService().listar(
        user_id=20, roles=["GerenteVentas"], limit=20
    )
    # Assert
    assert all(r["idusuariogerentenotificado"] == 20 for r in rows)
