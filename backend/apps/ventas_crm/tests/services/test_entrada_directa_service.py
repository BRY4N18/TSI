import pytest
from apps.ventas_crm.domain import ConflictError, ValidationError
from apps.ventas_crm.services.entrada_directa_service import EntradaDirectaService

pytestmark = pytest.mark.service

ADMIN_LOCAL = {"nombres": "Ana", "apellidos": "Admin", "gmail": "ana.admin@ex.com"}


def test_entrada_directa_rechaza_nit_existente():
    class Clientes:
        def exists_by_nit_any(self, nit): return True
    with pytest.raises(ConflictError):
        EntradaDirectaService(clientes=Clientes()).registrar(
            {"nombre": "A", "razon_social": "A", "tipo": "Proveedor", "nit_identificacion": "900",
             "admin_local": ADMIN_LOCAL}
        )


def test_entrada_directa_rechaza_admin_local_incompleto(mock_pinot, mock_kafka):
    with pytest.raises(ValidationError):
        EntradaDirectaService().registrar(
            {
                "nombre": "GAD",
                "razon_social": "GAD Demo",
                "tipo": "Municipio",
                "nit_identificacion": "1760777",
                "admin_local": {"nombres": "Ana"},
            }
        )


def test_entrada_directa_crea_admin_local_con_acceso(mock_pinot, mock_kafka):
    # Arrange / Act
    cliente = EntradaDirectaService().registrar(
        {
            "nombre": "GAD",
            "razon_social": "GAD Demo",
            "tipo": "Municipio",
            "nit_identificacion": "1760778",
            "admin_local": {"nombres": "Ana", "apellidos": "Admin", "gmail": "gad.admin@ex.com"},
        }
    )

    # Assert: el cliente nace con un admin local real, no huérfano.
    assert cliente["estado"] == "Activo"
    assert cliente["admin_local_id"] is not None

    from core.repositories.cuentas_clientes.credential_repository import CredentialRepository
    from core.repositories.cuentas_clientes.role_repository import RoleRepository
    from core.repositories.cuentas_clientes.user_repository import UserRepository

    user = UserRepository().find_by_id(cliente["admin_local_id"])
    assert user["gmail"] == "gad.admin@ex.com"
    assert CredentialRepository().find_by_user_id(cliente["admin_local_id"]) is not None
    assert "Cliente" in RoleRepository().get_user_roles(cliente["admin_local_id"])


def test_entrada_directa_rechaza_correo_admin_ya_registrado(mock_pinot, mock_kafka):
    # Arrange: primer registro consume el correo del admin.
    EntradaDirectaService().registrar(
        {
            "nombre": "GAD1",
            "razon_social": "GAD1",
            "tipo": "Municipio",
            "nit_identificacion": "1760779",
            "admin_local": {"nombres": "Ana", "apellidos": "Admin", "gmail": "dup.admin@ex.com"},
        }
    )
    # Act / Assert
    with pytest.raises(ConflictError):
        EntradaDirectaService().registrar(
            {
                "nombre": "GAD2",
                "razon_social": "GAD2",
                "tipo": "Municipio",
                "nit_identificacion": "1760780",
                "admin_local": {"nombres": "Ana", "apellidos": "Admin", "gmail": "dup.admin@ex.com"},
            }
        )
