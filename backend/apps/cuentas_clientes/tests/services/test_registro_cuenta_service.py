import pytest

from apps.cuentas_clientes.services.registro_cuenta_service import RegistroCuentaService


@pytest.mark.service
class TestRegistroCuentaService:
    def test_registrar_when_valid_creates_cliente(self, mock_pinot, mock_kafka):
        # Arrange
        service = RegistroCuentaService()
        data = {
            "razon_social": "Servicio Test S.A.",
            "nombre": "Servicio Test",
            "tipo": "Smart City",
            "nit_identificacion": "600111222-3",
            "fecha_inicio_contrato": 1704067200000,
            "admin_local": {
                "nombres": "Luis",
                "apellidos": "Test",
                "gmail": "luis.test@tsi.com",
            },
        }

        # Act
        result = service.registrar(user_id=1, roles=["Administrador"], data=data)

        # Assert
        assert result["estado"] == "Activo"
        assert result["admin_local_gmail"] == "luis.test@tsi.com"
        assert len(mock_kafka) >= 3

    def test_registrar_when_duplicate_nit_raises(self, mock_pinot, mock_kafka):
        # Arrange
        service = RegistroCuentaService()
        data = {
            "razon_social": "Dup",
            "nombre": "Dup",
            "tipo": "Municipio",
            "nit_identificacion": "900123456-1",
            "fecha_inicio_contrato": 1704067200000,
            "admin_local": {
                "nombres": "A",
                "apellidos": "B",
                "gmail": "unique@tsi.com",
            },
        }

        # Act / Assert
        with pytest.raises(Exception, match="NIT"):
            service.registrar(user_id=1, roles=["Administrador"], data=data)
