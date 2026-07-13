import pytest

from apps.cuentas_clientes.services.transferencia_propiedad_service import (
    TransferenciaPropiedadService,
)


@pytest.mark.service
class TestTransferenciaPropiedadService:
    def test_transferir_when_valid_updates_admin_local(self, mock_pinot, mock_kafka):
        # Arrange
        service = TransferenciaPropiedadService()

        # Act
        result = service.transferir(
            user_id=3,
            roles=["Cliente"],
            cliente_id=1,
            nuevo_responsable_id=4,
            ip_address="127.0.0.1",
        )

        # Assert
        assert result["nuevo_admin_local_id"] == 4
        assert result["admin_local_anterior_id"] == 3
