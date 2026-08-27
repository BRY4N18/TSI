"""User management service — CU-O04."""

from __future__ import annotations

from core.repositories.cuentas_clientes.credential_repository import (
    CredentialRepository,
)
from core.repositories.cuentas_clientes.cuenta_usuario_repository import (
    CuentaUsuarioRepository,
)
from core.repositories.cuentas_clientes.role_repository import RoleRepository
from core.repositories.cuentas_clientes.user_repository import UserRepository


class UserManagementError(Exception):
    """User management operation failed."""


class DatosInvalidosError(UserManagementError):
    """Entrada malformada. Se traduce a 400, no a 409.

    Existe separada de `UserManagementError` porque el conflicto de negocio
    («correo ya registrado») y la entrada malformada («falta el correo») son
    cosas distintas: la primera es 409, la segunda 400. Sin la distincion,
    `data["gmail"]` sobre un payload incompleto lanzaba `KeyError` y la peticion
    terminaba en **500** — el unico camino que no pasa por el manejador central y
    por tanto el unico sin garantias sobre lo que muestra (PG-SEC-007).
    """


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
        cuenta_usuario_repo: CuentaUsuarioRepository | None = None,
    ):
        self.user_repo = user_repo or UserRepository()
        self.role_repo = role_repo or RoleRepository()
        self.credential_repo = credential_repo or CredentialRepository()
        self.cuenta_usuario_repo = cuenta_usuario_repo or CuentaUsuarioRepository()

    def _require_admin(self, roles: list[str]) -> None:
        if self.ADMIN_ROLE not in roles:
            raise ForbiddenUserManagementError("Privilegios insuficientes")

    def list_users(self, *, admin_roles: list[str], cursor: str | None = None, limit: int = 20) -> list[dict]:
        self._require_admin(admin_roles)
        users = self.user_repo.list_users(cursor=cursor, limit=limit)
        # `get_user` ya adjunta `roles`; el listado no lo hacía y la pantalla de
        # gestión de cuenta (asignar/ver roles) mostraba "Sin rol" para TODOS
        # los usuarios, incluido el propio Administrador.
        for user in users:
            user["roles"] = self.role_repo.get_user_roles(user["idusuario"])
        return users

    def get_user(self, user_id: int, *, admin_roles: list[str]) -> dict:
        self._require_admin(admin_roles)
        user = self.user_repo.find_by_id(user_id)
        if not user:
            raise UserManagementError("Usuario no encontrado")
        user["roles"] = self.role_repo.get_user_roles(user_id)
        return user

    #: Campos sin los que `UserRepository.create` no puede construir la fila.
    CAMPOS_OBLIGATORIOS = ("nombres", "apellidos", "gmail")

    def create_user(self, data: dict, *, admin_roles: list[str]) -> dict:
        self._require_admin(admin_roles)

        if not isinstance(data, dict):
            raise DatosInvalidosError("El cuerpo debe ser un objeto JSON")
        faltantes = [c for c in self.CAMPOS_OBLIGATORIOS if not data.get(c)]
        if faltantes:
            raise DatosInvalidosError(
                f"Faltan campos obligatorios: {', '.join(faltantes)}"
            )

        if self.user_repo.find_by_gmail(data["gmail"]):
            raise UserManagementError("Correo ya registrado")

        user = self.user_repo.create(data)
        if "password" in data:
            self.credential_repo.create(user["idusuario"], data["password"])

        role_ids = data.get("role_ids", [])
        for role_id in role_ids:
            self.role_repo.assign_role_to_user(user["idusuario"], role_id)

        # Pertenencia a una cuenta cliente, si el alta la declara (decision #23).
        # Es **opcional**: los usuarios internos de TSI no pertenecen a ninguna
        # organizacion, y exigirlo dejaria sin poder crearlos.
        idcliente = data.get("idcliente")
        if idcliente:
            self.cuenta_usuario_repo.vincular(user["idusuario"], int(idcliente))
            user["idcliente"] = int(idcliente)

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
