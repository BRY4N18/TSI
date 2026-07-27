import pytest

from apps.ventas_crm.services.despacho_notificacion_ventas_service import (
    CanalNoDisponibleError,
    DespachoNotificacionVentasService,
)

pytestmark = pytest.mark.service


def test_despacho_slack_falla(mock_pinot, mock_kafka):
    # Arrange / Act / Assert
    with pytest.raises(CanalNoDisponibleError):
        DespachoNotificacionVentasService().despachar(
            {
                "id_prospecto": 1,
                "idusuariogerentenotificado": 20,
                "regladisparada": "x",
                "canal": "slack",
            }
        )
