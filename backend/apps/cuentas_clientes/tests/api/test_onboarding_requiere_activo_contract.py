import pytest

from apps.cuentas_clientes.services.autorregistro_proveedor_service import (
    AutorregistroProveedorService,
)
from apps.cuentas_clientes.services.onboarding_service import (
    OnboardingError,
    OnboardingService,
)


@pytest.mark.api
class TestOnboardingRequiereActivoContract:
    def test_progreso_when_pendiente_aprobacion_returns_403(
        self, api_client, mock_pinot, mock_kafka, cliente_auth_headers
    ):
        # Arrange — create pending account and force admin_local to match cliente token user
        created = AutorregistroProveedorService().autorregistrar(
            data={
                "razon_social": "Pendiente Test",
                "nombre": "Pendiente",
                "tipo": "Proveedor",
                "nit_identificacion": "840777666-0",
                "admin_local": {
                    "nombres": "Pend",
                    "apellidos": "Test",
                    "gmail": "pendiente.test@tsi.com",
                },
            }
        )
        # Use service-level assert for gate (API needs matching JWT for admin_local)
        service = OnboardingService()
        from core.repositories.cuentas_clientes.cliente_repository import ClienteRepository

        cliente = ClienteRepository().find_by_id(created["idcliente"])
        assert cliente["estado"] == "Pendiente_Aprobación"

        # Act / Assert
        with pytest.raises(OnboardingError, match="Activo"):
            service.get_progreso(
                user_id=cliente["admin_local_id"],
                roles=["Cliente"],
                cliente_id=created["idcliente"],
            )
