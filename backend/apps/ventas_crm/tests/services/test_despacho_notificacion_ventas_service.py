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


def test_despacho_email_va_al_gerente_no_al_prospecto(mock_pinot, mock_kafka, monkeypatch):
    # Arrange: el gmail del prospecto y el del gerente (idusuario=20) son distintos.
    sent = {}

    class FakeEmailSender:
        def send(self, *, event, cliente_id, gmail, subject, body):
            sent["gmail"] = gmail

    svc = DespachoNotificacionVentasService(email_sender=FakeEmailSender())
    # Act
    svc.despachar(
        {
            "id_prospecto": 999,
            "idusuariogerentenotificado": 20,
            "regladisparada": "tiempo_seccion_precios_5min",
            "canal": "email",
        }
    )
    # Assert: se envió al gmail del gerente (seed conftest), nunca a uno de prospecto.
    assert sent["gmail"] == "gerente.ventas@tsi.com"


def test_despacho_email_sin_gerente_notificado_falla(mock_pinot, mock_kafka):
    # Arrange / Act / Assert: gerente inexistente/sin gmail -> falla explícita, no envío silencioso.
    with pytest.raises(CanalNoDisponibleError):
        DespachoNotificacionVentasService().despachar(
            {
                "id_prospecto": 1,
                "idusuariogerentenotificado": 999999,
                "regladisparada": "x",
                "canal": "email",
            }
        )
