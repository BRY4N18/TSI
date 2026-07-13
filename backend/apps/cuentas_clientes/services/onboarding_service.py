"""Onboarding digital service — CU-O02 / CU-O09."""

from __future__ import annotations

from typing import Any

from apps.cuentas_clientes.services.audit_service import AuditService
from apps.cuentas_clientes.services.onboarding_access_service import OnboardingAccessService
from core.repositories.cuentas_clientes.cliente_repository import ClienteRepository
from core.repositories.cuentas_clientes.credential_repository import CredentialRepository
from core.repositories.cuentas_clientes.onboarding_repository import OnboardingRepository
from core.repositories.cuentas_clientes.preferencias_cliente_repository import (
    PreferenciasClienteRepository,
)

ETAPAS_OBLIGATORIAS = ["cambio_password", "perfil_corporativo", "preferencias"]


class OnboardingError(Exception):
    """Onboarding operation failed."""


class OnboardingService:
    """Manages onboarding progress and stage completion."""

    def __init__(
        self,
        cliente_repo: ClienteRepository | None = None,
        onboarding_repo: OnboardingRepository | None = None,
        credential_repo: CredentialRepository | None = None,
        preferencias_repo: PreferenciasClienteRepository | None = None,
        access: OnboardingAccessService | None = None,
        audit: AuditService | None = None,
    ):
        self.cliente_repo = cliente_repo or ClienteRepository()
        self.onboarding_repo = onboarding_repo or OnboardingRepository()
        self.credential_repo = credential_repo or CredentialRepository()
        self.preferencias_repo = preferencias_repo or PreferenciasClienteRepository()
        self.access = access or OnboardingAccessService()
        self.audit = audit or AuditService()

    def get_progreso(
        self,
        *,
        user_id: int,
        roles: list[str],
        cliente_id: int,
    ) -> dict[str, Any]:
        self.access.require_admin_local(user_id=user_id, roles=roles, cliente_id=cliente_id)
        cliente = self.cliente_repo.find_by_id(cliente_id)
        if not cliente:
            raise OnboardingError("Cuenta de cliente no encontrada")
        return self._build_progreso(cliente)

    def completar_etapa(
        self,
        *,
        user_id: int,
        roles: list[str],
        cliente_id: int,
        etapa: str,
        datos_etapa: dict[str, Any] | None = None,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        self.access.require_admin_local(user_id=user_id, roles=roles, cliente_id=cliente_id)
        cliente = self.cliente_repo.find_by_id(cliente_id)
        if not cliente:
            raise OnboardingError("Cuenta de cliente no encontrada")

        if etapa not in ETAPAS_OBLIGATORIAS:
            raise OnboardingError("etapa invalida")

        estado = cliente.get("estado_onboarding")
        if estado == "Completado":
            raise OnboardingError("Onboarding ya completado")

        if estado not in ("Pendiente", "En progreso", None):
            if estado is None and etapa != ETAPAS_OBLIGATORIAS[0]:
                raise OnboardingError("Debe configurar la cuenta antes del onboarding")

        existing = self.onboarding_repo.find_etapa(cliente_id, etapa)
        if existing and existing.get("completado"):
            raise OnboardingError("Etapa ya completada")

        self._validate_stage_order(cliente_id, etapa)
        self._process_stage_data(
            cliente_id=cliente_id,
            admin_local_id=cliente.get("admin_local_id"),
            etapa=etapa,
            datos_etapa=datos_etapa or {},
        )

        self.onboarding_repo.complete_etapa(cliente_id, etapa)

        progreso = self._build_progreso_after_completion(cliente_id, cliente)
        estado_onboarding = progreso["estado_onboarding"]
        if estado_onboarding != cliente.get("estado_onboarding"):
            self.cliente_repo.update(cliente_id, {"estado_onboarding": estado_onboarding})

        self.audit.log_onboarding_etapa(
            user_id=user_id,
            cliente_id=cliente_id,
            etapa=etapa,
            ip_address=ip_address,
        )

        return {"etapa": etapa, "progreso": progreso}

    def _validate_stage_order(self, cliente_id: int, etapa: str) -> None:
        idx = ETAPAS_OBLIGATORIAS.index(etapa)
        for prior in ETAPAS_OBLIGATORIAS[:idx]:
            row = self.onboarding_repo.find_etapa(cliente_id, prior)
            if not row or not row.get("completado"):
                raise OnboardingError("Debe completar la etapa anterior")

    def _process_stage_data(
        self,
        *,
        cliente_id: int,
        admin_local_id: int | None,
        etapa: str,
        datos_etapa: dict[str, Any],
    ) -> None:
        if etapa == "cambio_password":
            if not admin_local_id:
                raise OnboardingError("admin_local no asignado")
            cred = self.credential_repo.find_by_user_id(admin_local_id)
            if not cred:
                raise OnboardingError("Credencial no encontrada")
            if cred.get("estadocredencial") != "Activo":
                raise OnboardingError("Debe cambiar la contraseña antes de continuar")
            return

        if etapa == "perfil_corporativo":
            if not datos_etapa:
                raise OnboardingError("datos_etapa requeridos")
            updates: dict[str, Any] = {}
            for field in ("razon_social", "nombre", "logo_url"):
                if field in datos_etapa and datos_etapa[field] is not None:
                    updates[field] = datos_etapa[field]
            if not updates:
                raise OnboardingError("datos_etapa requeridos")
            if "razon_social" in updates and len(str(updates["razon_social"]).strip()) < 2:
                raise OnboardingError("razon_social invalida")
            self.cliente_repo.update(cliente_id, updates)
            return

        if etapa == "preferencias":
            if not datos_etapa:
                raise OnboardingError("datos_etapa requeridos")
            if self.preferencias_repo.find_by_cliente(cliente_id):
                raise OnboardingError("Preferencias ya existen")
            self.preferencias_repo.create(cliente_id, datos_etapa)

    def _build_progreso(self, cliente: dict[str, Any]) -> dict[str, Any]:
        cliente_id = cliente["idcliente"]
        rows = self.onboarding_repo.list_by_cliente(cliente_id)
        completadas = [
            r["etapa"]
            for r in rows
            if r.get("completado") and r["etapa"] in ETAPAS_OBLIGATORIAS
        ]
        etapa_actual = self._next_etapa(completadas)
        estado = cliente.get("estado_onboarding") or "Pendiente"
        if completadas and estado == "Pendiente":
            estado = "En progreso"
        if len(completadas) == len(ETAPAS_OBLIGATORIAS):
            estado = "Completado"
            etapa_actual = None
        return {
            "idcliente": cliente_id,
            "estado_onboarding": estado,
            "etapas_completadas": completadas,
            "etapa_actual": etapa_actual,
        }

    def _build_progreso_after_completion(
        self, cliente_id: int, cliente: dict[str, Any]
    ) -> dict[str, Any]:
        updated = self.cliente_repo.find_by_id(cliente_id) or cliente
        return self._build_progreso(updated)

    def _next_etapa(self, completadas: list[str]) -> str | None:
        for etapa in ETAPAS_OBLIGATORIAS:
            if etapa not in completadas:
                return etapa
        return None
