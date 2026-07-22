import pytest

from apps.cuentas_clientes.services.configuracion_cuenta_service import (
    ConfiguracionCuentaService,
)


@pytest.mark.service
class TestConfiguracionCuentaService:
    def test_configurar_when_valid_sets_pendiente(self, mock_pinot, mock_kafka):
        # Arrange
        from apps.cuentas_clientes.services.registro_cuenta_service import (
            RegistroCuentaService,
        )

        registro = RegistroCuentaService()
        created = registro.registrar(
            user_id=1,
            roles=["Administrador"],
            data={
                "razon_social": "Config Svc S.A.",
                "nombre": "Config",
                "tipo": "Municipio",
                "nit_identificacion": "802345678-9",
                "fecha_inicio_contrato": 1704067200000,
                "admin_local": {
                    "nombres": "Svc",
                    "apellidos": "Admin",
                    "gmail": "svc.config@tsi.com",
                },
            },
        )
        service = ConfiguracionCuentaService()

        # Act
        result = service.configurar(
            user_id=1,
            roles=["Administrador"],
            cliente_id=created["idcliente"],
            data={"plan_suscripcion": "basico"},
        )

        # Assert
        assert result["estado_onboarding"] == "Pendiente"
        assert result["plan_suscripcion"] == "basico"
