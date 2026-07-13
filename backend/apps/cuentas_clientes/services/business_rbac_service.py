"""Business RBAC service — CU-O13."""

from __future__ import annotations

from core.repositories.cuentas_clientes.role_repository import RoleRepository


class BusinessRBACError(Exception):
    """RBAC operation failed."""


class ForbiddenRBACError(BusinessRBACError):
    """Caller lacks Administrator role."""


class BusinessRBACService:
    """Manages business roles and user-role assignments."""

    ADMIN_ROLE = "Administrador"

    def __init__(self, role_repo: RoleRepository | None = None):
        self.role_repo = role_repo or RoleRepository()

    def _require_admin(self, roles: list[str]) -> None:
        if self.ADMIN_ROLE not in roles:
            raise ForbiddenRBACError("Privilegios insuficientes")

    def list_roles(self, *, admin_roles: list[str]) -> list[dict]:
        self._require_admin(admin_roles)
        return self.role_repo.list_roles()

    def create_role(self, data: dict, *, admin_roles: list[str]) -> dict:
        self._require_admin(admin_roles)
        if self.role_repo.find_role_by_name(data["rol"]):
            raise BusinessRBACError("Rol ya existe")
        return self.role_repo.create_role(data)

    def update_role(self, role_id: int, data: dict, *, admin_roles: list[str]) -> dict:
        self._require_admin(admin_roles)
        role = self.role_repo.update_role(role_id, data)
        if not role:
            raise BusinessRBACError("Rol no encontrado")
        return role

    def deactivate_role(self, role_id: int, *, admin_roles: list[str]) -> dict:
        self._require_admin(admin_roles)
        role = self.role_repo.deactivate_role(role_id)
        if not role:
            raise BusinessRBACError("Rol no encontrado")
        return role

    def assign_role(self, user_id: int, role_id: int, *, admin_roles: list[str]) -> dict:
        self._require_admin(admin_roles)
        role = self.role_repo.find_role_by_id(role_id)
        if not role:
            raise BusinessRBACError("Rol no encontrado")
        return self.role_repo.assign_role_to_user(user_id, role_id)
