from unittest.mock import patch

import pytest

from apps.cuentas_clientes.services.aprobacion_proveedor_service import (
    AprobacionProveedorService,
)
from apps.cuentas_clientes.services.autorregistro_proveedor_service import (
    AutorregistroProveedorService,
)
from apps.cuentas_clientes.services.onboarding_notificacion_service import (
    OnboardingNotificacionService,
)


@pytest.mark.service
class TestOnboardingNotificacionService:
    @patch("core.notificaciones.email_sender.send_mail")
    def test_notify_invitacion_does_not_raise(self, mock_send, mock_pinot, mock_kafka):
        # Arrange
        service = OnboardingNotificacionService()

        # Act / Assert
        service.notify_invitacion(
            cliente_id=1,
            user_id=3,
            temp_password="temp123",
            actor_id=1,
        )

    @patch("core.notificaciones.email_sender.send_mail")
    def test_notify_reminder_does_not_raise(self, mock_send, mock_pinot, mock_kafka):
        # Arrange
        service = OnboardingNotificacionService()

        # Act / Assert
        service.notify_reminder(cliente_id=1, admin_local_id=3)

    @patch("core.notificaciones.email_sender.send_mail")
    def test_notify_aprobacion_does_not_raise(self, mock_send, mock_pinot, mock_kafka):
        # Arrange
        service = OnboardingNotificacionService()

        # Act
        service.notify_aprobacion(cliente_id=1, admin_local_id=3, actor_id=1)

        # Assert
        mock_send.assert_called_once()

    @patch("core.notificaciones.email_sender.send_mail")
    def test_notify_rechazo_does_not_raise(self, mock_send, mock_pinot, mock_kafka):
        # Arrange
        service = OnboardingNotificacionService()

        # Act
        service.notify_rechazo(
            cliente_id=1,
            admin_local_id=3,
            actor_id=1,
            motivo="Documentacion incompleta",
        )

        # Assert
        mock_send.assert_called_once()


@pytest.mark.service
class TestAprobacionNotificaEmail:
    def _solicitud(self):
        return AutorregistroProveedorService().autorregistrar(
            data={
                "razon_social": "Mail Test CIA",
                "nombre": "Mail Test",
                "tipo": "Proveedor",
                "nit_identificacion": "840555666-8",
                "admin_local": {
                    "nombres": "Mail",
                    "apellidos": "User",
                    "gmail": "mail.user@tsi.com",
                },
            }
        )

    @patch.object(OnboardingNotificacionService, "notify_aprobacion")
    def test_decidir_aprobar_dispara_notify(
        self, mock_notify, mock_pinot, mock_kafka
    ):
        # Arrange
        created = self._solicitud()
        service = AprobacionProveedorService()

        # Act
        service.decidir(
            user_id=1,
            roles=["Administrador"],
            cliente_id=created["idcliente"],
            decision="aprobar",
        )

        # Assert
        mock_notify.assert_called_once()

    @patch.object(OnboardingNotificacionService, "notify_rechazo")
    def test_decidir_rechazar_dispara_notify(
        self, mock_notify, mock_pinot, mock_kafka
    ):
        # Arrange
        created = self._solicitud()
        service = AprobacionProveedorService()

        # Act
        service.decidir(
            user_id=1,
            roles=["Administrador"],
            cliente_id=created["idcliente"],
            decision="rechazar",
            motivo="Falta documentacion",
        )

        # Assert
        mock_notify.assert_called_once()
        assert mock_notify.call_args.kwargs["motivo"] == "Falta documentacion"
