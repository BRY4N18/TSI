"""Access helpers for Proveedor (admin_local of Activo Dim_Cliente)."""

from __future__ import annotations

from typing import Any

from core.repositories.cuentas_clientes.cliente_repository import ClienteRepository

ROLE_CLIENTE = "Cliente"
ROLE_PROVEEDOR = "Proveedor"


class ProveedorAccessError(Exception):
    """Proveedor flota access denied."""


class ProveedorAccessService:
    """Resolves ownership for red_operativa unit CRUD."""

    def __init__(self, cliente_repo: ClienteRepository | None = None):
        self.cliente_repo = cliente_repo or ClienteRepository()

    def resolve_cliente_activo(self, *, user_id: int, roles: list[str]) -> dict[str, Any]:
        if ROLE_CLIENTE not in roles and ROLE_PROVEEDOR not in roles:
            raise ProveedorAccessError("Se requiere rol de Proveedor/Cliente")
        cliente = self.cliente_repo.find_by_admin_local(user_id)
        if not cliente:
            raise ProveedorAccessError("Usuario no es administrador local de ninguna cuenta")
        if cliente.get("estado") != "Activo":
            raise ProveedorAccessError("La cuenta del proveedor no esta Activa")
        return cliente

    def require_unidad_propia(
        self, *, user_id: int, roles: list[str], unidad: dict[str, Any] | None
    ) -> dict[str, Any]:
        if not unidad:
            raise LookupError("Unidad no encontrada")
        cliente = self.resolve_cliente_activo(user_id=user_id, roles=roles)
        if int(unidad.get("idcliente") or 0) != int(cliente["idcliente"]):
            raise ProveedorAccessError("La unidad no pertenece a este proveedor")
        return cliente
