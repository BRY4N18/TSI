import pytest

from apps.cuentas_clientes.services.cuenta_preferencias_service import (
    CuentaPreferenciasService,
)


@pytest.mark.service
class TestCuentaPreferenciasService:
    def test_get_preferencias_when_exists_returns_data(self, mock_pinot, mock_kafka):
        # Arrange
        service = CuentaPreferenciasService()

        # Act
        result = service.get_preferencias(user_id=3, roles=["Cliente"], cliente_id=1)

        # Assert
        assert result["id_cliente"] == 1

    def test_update_preferencias_when_valid_updates_telefono(self, mock_pinot, mock_kafka):
        # Arrange
        service = CuentaPreferenciasService()

        # Act
        result = service.update_preferencias(
            user_id=3,
            roles=["Cliente"],
            cliente_id=1,
            data={"telefono_sms": "3005554433", "canales_notificacion": "sms"},
            ip_address="127.0.0.1",
        )

        # Assert
        assert result["preferencias"]["telefono_sms"] == "3005554433"
