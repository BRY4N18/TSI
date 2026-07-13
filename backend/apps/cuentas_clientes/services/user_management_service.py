"""User management service — CU-O04."""

from __future__ import annotations

from core.repositories.cuentas_clientes.credential_repository import CredentialRepository
from core.repositories.cuentas_clientes.role_repository import RoleRepository
from core.repositories.cuentas_clientes.user_repository import UserRepository


class UserManagementError(Exception):
    """User management operation failed."""


class ForbiddenUserManagementError(UserManagementError):
    """Caller lacks Administrator role."""


class UserManagementService:
    """CRUD operations for Dim_Usuarios (admin only)."""

    ADMIN_ROLE = "Administrador"

    def __init__(
        self,
        user_repo: UserRepository | None = None,
        role_repo: RoleRepository | None = None,
        credential_repo: CredentialRepository | None = None,
    ):
        self.user_repo = user_repo or UserRepository()
        self.role_repo = role_repo or RoleRepository()
        self.credential_repo = credential_repo or CredentialRepository()

    def _require_admin(self, roles: list[str]) -> None:
        if self.ADMIN_ROLE not in roles:
            raise ForbiddenUserManagementError("Privilegios insuficientes")

    def list_users(self, *, admin_roles: list[str], cursor: str | None = None, limit: int = 20) -> list[dict]:
        self._require_admin(admin_roles)
        return self.user_repo.list_users(cursor=cursor, limit=limit)

    def get_user(self, user_id: int, *, admin_roles: list[str]) -> dict:
        self._require_admin(admin_roles)
        user = self.user_repo.find_by_id(user_id)
        if not user:
            raise UserManagementError("Usuario no encontrado")
        user["roles"] = self.role_repo.get_user_roles(user_id)
        return user

    def create_user(self, data: dict, *, admin_roles: list[str]) -> dict:
        self._require_admin(admin_roles)
        if self.user_repo.find_by_gmail(data["gmail"]):
            raise UserManagementError("Correo ya registrado")

        user = self.user_repo.create(data)
        if "password" in data:
            self.credential_repo.create(user["idusuario"], data["password"])

        role_ids = data.get("role_ids", [])
        for role_id in role_ids:
            self.role_repo.assign_role_to_user(user["idusuario"], role_id)

        user["roles"] = self.role_repo.get_user_roles(user["idusuario"])
        return user

    def update_user(self, user_id: int, data: dict, *, admin_roles: list[str]) -> dict:
        self._require_admin(admin_roles)
        user = self.user_repo.update(user_id, data)
        if not user:
            raise UserManagementError("Usuario no encontrado")

        role_ids = data.get("role_ids")
        if role_ids is not None:
            for role_id in role_ids:
                self.role_repo.assign_role_to_user(user_id, role_id)

        user["roles"] = self.role_repo.get_user_roles(user_id)
        return user

    def deactivate_user(self, user_id: int, *, admin_roles: list[str]) -> dict:
        self._require_admin(admin_roles)
        user = self.user_repo.deactivate(user_id)
        if not user:
            raise UserManagementError("Usuario no encontrado")
        return user
