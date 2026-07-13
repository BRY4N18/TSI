"""Access control helpers for cuenta de cliente operations."""

from __future__ import annotations

from core.repositories.cuentas_clientes.cliente_repository import ClienteRepository
from core.repositories.cuentas_clientes.cuenta_usuario_repository import CuentaUsuarioRepository


class CuentaAccessError(Exception):
    """Access denied to cuenta resource."""


class CuentaAccessService:
    """Authorization rules for gestion-cuenta (RNF-CTA-002)."""

    ADMIN_ROLE = "Administrador"
    CLIENTE_ROLE = "Cliente"

    def __init__(
        self,
        cliente_repo: ClienteRepository | None = None,
        cuenta_usuario_repo: CuentaUsuarioRepository | None = None,
    ):
        self.cliente_repo = cliente_repo or ClienteRepository()
        self.cuenta_usuario_repo = cuenta_usuario_repo or CuentaUsuarioRepository()

    def require_access(self, *, user_id: int, roles: list[str], cliente_id: int) -> None:
        if not self.can_access_cuenta(user_id=user_id, roles=roles, cliente_id=cliente_id):
            raise CuentaAccessError("Privilegios insuficientes")

    def can_access_cuenta(self, *, user_id: int, roles: list[str], cliente_id: int) -> bool:
        if self.ADMIN_ROLE in roles:
            return True
        if self.CLIENTE_ROLE in roles:
            return self.cuenta_usuario_repo.user_belongs_to_cliente(user_id, cliente_id)
        return False

    def require_admin_local(self, *, user_id: int, cliente_id: int) -> None:
        if not self.is_admin_local(user_id=user_id, cliente_id=cliente_id):
            raise CuentaAccessError("No es administrador local de esta cuenta")

    def is_admin_local(self, *, user_id: int, cliente_id: int) -> bool:
        cliente = self.cliente_repo.find_by_id(cliente_id)
        if not cliente:
            return False
        return cliente.get("admin_local_id") == user_id

    def require_admin_global(self, roles: list[str]) -> None:
        if self.ADMIN_ROLE not in roles:
            raise CuentaAccessError("Privilegios insuficientes")

    def ensure_cuenta_activa(self, cliente_id: int) -> dict:
        cliente = self.cliente_repo.find_by_id(cliente_id)
        if not cliente:
            raise CuentaAccessError("Cuenta de cliente no encontrada")
        if cliente.get("estado") == "Dado de baja":
            raise CuentaAccessError("La cuenta ya está dada de baja")
        return cliente
