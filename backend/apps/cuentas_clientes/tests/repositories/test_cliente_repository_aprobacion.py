import pytest

from apps.cuentas_clientes.onboarding_permissions import OnboardingPermissions
from core.repositories.cuentas_clientes.cliente_repository import ClienteRepository


@pytest.mark.repository
class TestClienteRepositoryAprobacion:
    def test_list_by_estado_and_update_estado(self, mock_pinot, mock_kafka):
        # Arrange
        repo = ClienteRepository()
        created = repo.create(
            {
                "razon_social": "Repo Test",
                "nombre": "Repo",
                "tipo": "Proveedor",
                "nit_identificacion": "850111000-9",
                "admin_local_id": 99,
                "estado": "Pendiente_Aprobación",
            }
        )

        # Act
        pending = repo.list_by_estado("Pendiente_Aprobación")
        updated = repo.update_estado(
            created["idcliente"],
            estado="Activo",
            estado_onboarding="Pendiente",
        )

        # Assert
        assert any(c["idcliente"] == created["idcliente"] for c in pending)
        assert updated["estado"] == "Activo"
        assert updated["estado_onboarding"] == "Pendiente"


@pytest.mark.unit
class TestOnboardingPermissionsProveedor:
    def test_can_autorregistrar_is_public(self):
        assert OnboardingPermissions.can_autorregistrar() is True

    def test_can_aprobar_requires_admin(self):
        assert OnboardingPermissions.can_aprobar(["Administrador"]) is True
        assert OnboardingPermissions.can_aprobar(["Cliente"]) is False
