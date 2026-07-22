from unittest.mock import patch

import pytest

from apps.cuentas_clientes.services.onboarding_reminder_service import (
    OnboardingReminderService,
)


@pytest.mark.service
class TestOnboardingReminderService:
    def test_list_eligible_clientes_when_old_incomplete_returns_cliente(
        self, mock_pinot, mock_kafka
    ):
        # Arrange
        PINOT_STORE = __import__("conftest", fromlist=["PINOT_STORE"]).PINOT_STORE
        PINOT_STORE["Dim_Cliente"].append(
            {
                "idcliente": 99,
                "nombre": "Old",
                "razon_social": "Old S.A.",
                "tipo": "Municipio",
                "nit_identificacion": "111",
                "estado_onboarding": "Pendiente",
                "estado": "Activo",
                "admin_local_id": 3,
                "fecha_inicio_contrato": 1,
                "fecha_actualizacion": "2020-01-01T00:00:00+00:00",
            }
        )
        service = OnboardingReminderService()

        # Act
        eligible = service.list_eligible_clientes()

        # Assert
        ids = [c["idcliente"] for c in eligible]
        assert 99 in ids

    @patch("core.notificaciones.email_sender.send_mail")
    def test_send_reminders_returns_count(self, mock_send, mock_pinot, mock_kafka):
        # Arrange
        PINOT_STORE = __import__("conftest", fromlist=["PINOT_STORE"]).PINOT_STORE
        PINOT_STORE["Dim_Cliente"].append(
            {
                "idcliente": 100,
                "nombre": "Reminder",
                "razon_social": "Reminder S.A.",
                "tipo": "Aseguradora",
                "nit_identificacion": "222",
                "estado_onboarding": "En progreso",
                "estado": "Activo",
                "admin_local_id": 3,
                "fecha_inicio_contrato": 1,
                "fecha_actualizacion": "2020-01-01T00:00:00+00:00",
            }
        )
        service = OnboardingReminderService()

        # Act
        sent = service.send_reminders()

        # Assert
        assert sent >= 1
