"""Cuenta preferencias service — CU-O03."""

from __future__ import annotations

from typing import Any

from apps.cuentas_clientes.services.audit_service import AuditService
from apps.cuentas_clientes.services.cuenta_access_service import CuentaAccessService
from core.repositories.cuentas_clientes.preferencias_cliente_repository import (
    PreferenciasClienteRepository,
)

EDITABLE_FIELDS = {
    "umbrales_alerta",
    "canales_notificacion",
    "telefono_sms",
    "zonas_geograficas",
    "destinatarios_reportes",
    "frecuencia_reportes",
    "formato_reportes",
}


class CuentaPreferenciasError(Exception):
    """Preferencias update failed."""


class CuentaPreferenciasService:
    """Manages operational preferences on Dim_Preferencias_Cliente."""

    def __init__(
        self,
        preferencias_repo: PreferenciasClienteRepository | None = None,
        access: CuentaAccessService | None = None,
        audit: AuditService | None = None,
    ):
        self.preferencias_repo = preferencias_repo or PreferenciasClienteRepository()
        self.access = access or CuentaAccessService()
        self.audit = audit or AuditService()

    def get_preferencias(
        self, *, user_id: int, roles: list[str], cliente_id: int
    ) -> dict[str, Any]:
        self.access.require_access(user_id=user_id, roles=roles, cliente_id=cliente_id)
        preferencias = self.preferencias_repo.find_by_cliente(cliente_id)
        if not preferencias:
            raise CuentaPreferenciasError("Preferencias no encontradas")
        return self._serialize(preferencias)

    def update_preferencias(
        self,
        *,
        user_id: int,
        roles: list[str],
        cliente_id: int,
        data: dict[str, Any],
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        self.access.require_access(user_id=user_id, roles=roles, cliente_id=cliente_id)
        self.access.ensure_cuenta_activa(cliente_id)

        preferencias = self.preferencias_repo.find_by_cliente(cliente_id)
        if not preferencias:
            raise CuentaPreferenciasError("Preferencias no encontradas")

        updates = {k: v for k, v in data.items() if k in EDITABLE_FIELDS and v is not None}
        if not updates:
            raise CuentaPreferenciasError("Campos invalidos")

        canales = updates.get("canales_notificacion", preferencias.get("canales_notificacion"))
        telefono = updates.get("telefono_sms", preferencias.get("telefono_sms"))
        if canales in ("sms", "ambos") and not telefono:
            raise CuentaPreferenciasError("telefono_sms requerido para canal SMS")

        for field, new_value in updates.items():
            old_value = preferencias.get(field)
            if old_value != new_value:
                self.audit.log_cuenta_field_change(
                    user_id=user_id,
                    cliente_id=cliente_id,
                    field=f"preferencias.{field}",
                    old_value=old_value,
                    new_value=new_value,
                    ip_address=ip_address,
                )

        updated = self.preferencias_repo.update(preferencias["id_preferencia"], updates)
        if not updated:
            raise CuentaPreferenciasError("Preferencias no encontradas")

        return {
            "message": "Preferencias actualizadas",
            "preferencias": self._serialize(updated),
        }

    def _serialize(self, preferencias: dict[str, Any]) -> dict[str, Any]:
        return {
            "id_preferencia": preferencias["id_preferencia"],
            "id_cliente": preferencias["id_cliente"],
            "umbrales_alerta": preferencias.get("umbrales_alerta", ""),
            "canales_notificacion": preferencias.get("canales_notificacion", "email"),
            "telefono_sms": preferencias.get("telefono_sms"),
            "zonas_geograficas": preferencias.get("zonas_geograficas", ""),
            "destinatarios_reportes": preferencias.get("destinatarios_reportes", ""),
            "frecuencia_reportes": preferencias.get("frecuencia_reportes", ""),
            "formato_reportes": preferencias.get("formato_reportes", "PDF"),
        }
