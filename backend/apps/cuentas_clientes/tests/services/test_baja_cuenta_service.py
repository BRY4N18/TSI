import pytest

from apps.cuentas_clientes.services.baja_cuenta_service import BajaCuentaService


@pytest.mark.service
class TestBajaCuentaService:
    def test_dar_baja_when_admin_expels_sessions(self, mock_pinot, mock_kafka):
        # Arrange
        service = BajaCuentaService()

        # Act
        result = service.dar_baja(
            user_id=1,
            roles=["Administrador"],
            cliente_id=1,
            motivo="Test baja",
            ip_address="127.0.0.1",
        )

        # Assert
        assert result["estado"] == "Dado de baja"
        assert result["sesiones_expulsadas"] >= 1
