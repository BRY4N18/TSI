import pytest

from apps.cuentas_clientes.services.cuenta_perfil_service import CuentaPerfilService


@pytest.mark.service
class TestCuentaPerfilService:
    def test_get_perfil_when_cliente_has_access_returns_data(self, mock_pinot, mock_kafka):
        # Arrange
        service = CuentaPerfilService()

        # Act
        result = service.get_perfil(user_id=3, roles=["Cliente"], cliente_id=1)

        # Assert
        assert result["idcliente"] == 1
        assert result["razon_social"] == "Empresa Demo S.A.S."

    def test_update_perfil_when_valid_updates_fields(self, mock_pinot, mock_kafka):
        # Arrange
        service = CuentaPerfilService()

        # Act
        result = service.update_perfil(
            user_id=3,
            roles=["Cliente"],
            cliente_id=1,
            data={"nombre": "Nuevo Nombre"},
            ip_address="127.0.0.1",
        )

        # Assert
        assert "nombre" in result["campos_modificados"]
        assert result["perfil"]["nombre"] == "Nuevo Nombre"
