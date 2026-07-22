"""Server access service — CU-O15."""

from __future__ import annotations

from core.repositories.cuentas_clientes.server_access_repository import (
    ServerAccessRepository,
)


class ServerAccessError(Exception):
    """Server access operation failed."""


class ForbiddenServerAccessError(ServerAccessError):
    """Caller lacks required role."""


class ServerAccessService:
    """Manages server-level users, roles and assignments."""

    ALLOWED_ROLES = {"Administrador", "Director Tecnológico"}

    def __init__(self, repo: ServerAccessRepository | None = None):
        self.repo = repo or ServerAccessRepository()

    def _require_access(self, roles: list[str]) -> None:
        if not self.ALLOWED_ROLES.intersection(roles):
            raise ForbiddenServerAccessError("Privilegios insuficientes")

    def list_server_users(self, *, caller_roles: list[str]) -> list[dict]:
        self._require_access(caller_roles)
        return self.repo.list_server_users()

    def create_server_user(self, data: dict, *, caller_roles: list[str]) -> dict:
        self._require_access(caller_roles)
        return self.repo.create_server_user(data)

    def update_server_user(self, server_user_id: int, data: dict, *, caller_roles: list[str]) -> dict:
        self._require_access(caller_roles)
        user = self.repo.update_server_user(server_user_id, data)
        if not user:
            raise ServerAccessError("Usuario de servidor no encontrado")
        return user

    def list_server_roles(self, *, caller_roles: list[str]) -> list[dict]:
        self._require_access(caller_roles)
        return self.repo.list_server_roles()

    def create_server_role(self, data: dict, *, caller_roles: list[str]) -> dict:
        self._require_access(caller_roles)
        return self.repo.create_server_role(data)

    def update_server_role(self, server_role_id: int, data: dict, *, caller_roles: list[str]) -> dict:
        self._require_access(caller_roles)
        role = self.repo.update_server_role(server_role_id, data)
        if not role:
            raise ServerAccessError("Rol de servidor no encontrado")
        return role

    def assign_server_role(
        self, server_user_id: int, server_role_id: int, *, caller_roles: list[str]
    ) -> dict:
        self._require_access(caller_roles)
        return self.repo.assign_server_role(server_user_id, server_role_id)

    def map_server_role_to_app_role(
        self, server_role_id: int, app_role_id: int, *, caller_roles: list[str]
    ) -> dict:
        self._require_access(caller_roles)
        return self.repo.map_server_role_to_app_role(server_role_id, app_role_id)
