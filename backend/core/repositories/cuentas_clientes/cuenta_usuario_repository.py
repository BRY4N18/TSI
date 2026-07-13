"""Membership repository — usuario to cliente account via admin_local_id only."""

from __future__ import annotations

from typing import Any

from core.pinot.client import PinotClient
from core.repositories.cuentas_clientes.cliente_repository import ClienteRepository
from core.repositories.cuentas_clientes.user_repository import UserRepository


class CuentaUsuarioRepository:
    """Resolves which users belong to a cliente account (admin local only)."""

    def __init__(
        self,
        pinot: PinotClient | None = None,
        user_repo: UserRepository | None = None,
        cliente_repo: ClienteRepository | None = None,
    ):
        pinot = pinot or PinotClient()
        self.user_repo = user_repo or UserRepository(pinot=pinot)
        self.cliente_repo = cliente_repo or ClienteRepository(pinot=pinot)

    def list_active_by_cliente(self, cliente_id: int) -> list[dict[str, Any]]:
        cliente = self.cliente_repo.find_by_id(cliente_id)
        if not cliente:
            return []
        admin_id = cliente.get("admin_local_id")
        if not admin_id:
            return []
        user = self.user_repo.find_by_id(admin_id)
        if user and user.get("activo", False):
            return [user]
        return []

    def user_belongs_to_cliente(self, user_id: int, cliente_id: int) -> bool:
        cliente = self.cliente_repo.find_by_id(cliente_id)
        if not cliente:
            return False
        return cliente.get("admin_local_id") == user_id

    def get_cliente_ids_for_user(self, user_id: int) -> list[int]:
        cliente = self.cliente_repo.find_by_admin_local(user_id)
        if cliente:
            return [cliente["idcliente"]]
        return []
