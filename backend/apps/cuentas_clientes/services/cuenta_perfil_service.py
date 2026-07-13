"""Cuenta perfil service — CU-O03."""

from __future__ import annotations

from typing import Any

from apps.cuentas_clientes.services.audit_service import AuditService
from apps.cuentas_clientes.services.cuenta_access_service import CuentaAccessService
from core.repositories.cuentas_clientes.cliente_repository import ClienteRepository

READONLY_FIELDS = {"tipo", "nit_identificacion", "estado", "admin_local_id", "idcliente"}
EDITABLE_FIELDS = {"razon_social", "nombre", "logo_url"}


class CuentaPerfilError(Exception):
    """Perfil update failed."""


class CuentaPerfilService:
    """Manages corporate profile updates on Dim_Cliente."""

    def __init__(
        self,
        cliente_repo: ClienteRepository | None = None,
        access: CuentaAccessService | None = None,
        audit: AuditService | None = None,
    ):
        self.cliente_repo = cliente_repo or ClienteRepository()
        self.access = access or CuentaAccessService()
        self.audit = audit or AuditService()

    def get_perfil(self, *, user_id: int, roles: list[str], cliente_id: int) -> dict[str, Any]:
        self.access.require_access(user_id=user_id, roles=roles, cliente_id=cliente_id)
        cliente = self.cliente_repo.find_by_id(cliente_id)
        if not cliente:
            raise CuentaPerfilError("Cuenta de cliente no encontrada")
        return self._serialize_perfil(cliente)

    def update_perfil(
        self,
        *,
        user_id: int,
        roles: list[str],
        cliente_id: int,
        data: dict[str, Any],
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        self.access.require_access(user_id=user_id, roles=roles, cliente_id=cliente_id)
        cliente = self.access.ensure_cuenta_activa(cliente_id)

        updates: dict[str, Any] = {}
        for field, value in data.items():
            if field in READONLY_FIELDS:
                continue
            if field in EDITABLE_FIELDS and value is not None:
                updates[field] = value

        if not updates:
            raise CuentaPerfilError("Campos invalidos")

        if "razon_social" in updates and len(str(updates["razon_social"]).strip()) < 2:
            raise CuentaPerfilError("razon_social invalida")

        campos_modificados = []
        for field, new_value in updates.items():
            old_value = cliente.get(field)
            if old_value != new_value:
                campos_modificados.append(field)
                self.audit.log_cuenta_field_change(
                    user_id=user_id,
                    cliente_id=cliente_id,
                    field=field,
                    old_value=old_value,
                    new_value=new_value,
                    ip_address=ip_address,
                )

        updated = self.cliente_repo.update(cliente_id, updates)
        if not updated:
            raise CuentaPerfilError("Cuenta de cliente no encontrada")

        return {
            "message": "Perfil actualizado",
            "campos_modificados": campos_modificados,
            "perfil": self._serialize_perfil(updated),
        }

    def _serialize_perfil(self, cliente: dict[str, Any]) -> dict[str, Any]:
        return {
            "idcliente": cliente["idcliente"],
            "razon_social": cliente.get("razon_social", ""),
            "nombre": cliente.get("nombre", ""),
            "tipo": cliente.get("tipo", ""),
            "nit_identificacion": cliente.get("nit_identificacion", ""),
            "logo_url": cliente.get("logo_url"),
            "estado": cliente.get("estado", "Activo"),
            "admin_local_id": cliente.get("admin_local_id"),
        }
