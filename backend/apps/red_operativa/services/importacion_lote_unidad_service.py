"""CU-O56 — importación en lote todo-o-nada (unidades + credenciales)."""

from __future__ import annotations

import re
import secrets
from typing import Any

from apps.cuentas_clientes.services.onboarding_notificacion_service import (
    OnboardingNotificacionService,
)
from apps.red_operativa.services.proveedor_access_service import ProveedorAccessService
from apps.red_operativa.services.registro_unidad_service import RegistroUnidadService
from core.repositories.cuentas_clientes.credential_repository import CredentialRepository
from core.repositories.cuentas_clientes.role_repository import RoleRepository
from core.repositories.cuentas_clientes.user_repository import UserRepository

MAX_FILAS = 500
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
UNIDAD_ROLE = "Unidad"


class ImportacionLoteUnidadService:
    def __init__(
        self,
        registro_service: RegistroUnidadService | None = None,
        access: ProveedorAccessService | None = None,
        user_repo: UserRepository | None = None,
        credential_repo: CredentialRepository | None = None,
        role_repo: RoleRepository | None = None,
        notificacion: OnboardingNotificacionService | None = None,
    ):
        self.registro_service = registro_service or RegistroUnidadService()
        self.access = access or ProveedorAccessService()
        self.user_repo = user_repo or UserRepository()
        self.credential_repo = credential_repo or CredentialRepository()
        self.role_repo = role_repo or RoleRepository()
        self.notificacion = notificacion or OnboardingNotificacionService()

    def importar(
        self,
        filas: list[dict[str, Any]],
        *,
        user_id: int,
        roles: list[str],
    ) -> dict[str, Any]:
        if len(filas) > MAX_FILAS:
            raise ValueError(f"El archivo excede el límite de {MAX_FILAS} unidades")

        cliente = self.access.resolve_cliente_activo(user_id=user_id, roles=roles)
        idcliente = cliente["idcliente"]

        unidad_role = self.role_repo.find_role_by_name(UNIDAD_ROLE)
        if not unidad_role or not unidad_role.get("activo", True):
            return {
                "insertadas": 0,
                "usuarios_creados": 0,
                "fallidas": [
                    {
                        "fila": 0,
                        "motivo": f"Rol '{UNIDAD_ROLE}' no configurado o inactivo",
                    }
                ],
            }

        placas_en_archivo: set[str] = set()
        gmails_en_archivo: set[str] = set()
        fallidas: list[dict[str, Any]] = []
        preparadas: list[dict[str, Any]] = []

        for i, fila in enumerate(filas, start=1):
            try:
                payload = dict(fila)
                payload.pop("idcliente", None)
                payload["idcliente"] = idcliente
                if not payload.get("tipopropiedad"):
                    payload["tipopropiedad"] = "Externa"
                gmail = str(payload.get("gmail", "")).strip().lower()
                if not gmail or not EMAIL_RE.match(gmail):
                    raise KeyError("gmail invalido o faltante")
                if gmail in gmails_en_archivo:
                    raise ValueError(f"gmail {gmail} duplicado dentro del archivo")
                existing_user = self.user_repo.find_by_gmail(gmail)
                if existing_user and existing_user.get("activo", True):
                    raise ValueError(f"Correo ya registrado: {gmail}")

                self.registro_service._validar(payload)
                placa = payload["placa"]
                if placa in placas_en_archivo:
                    raise ValueError(f"placa {placa} duplicada dentro del archivo")
                if self.registro_service.unidad_repo.find_by_placa_activa(placa):
                    raise ValueError(f"Ya existe una unidad activa con placa {placa}")
                if not self.registro_service.unidad_repo.condado_exists(payload["idcondado"]):
                    raise LookupError(f"idcondado {payload['idcondado']} no existe")

                placas_en_archivo.add(placa)
                gmails_en_archivo.add(gmail)
                preparadas.append({**payload, "gmail": gmail})
            except (KeyError, ValueError, LookupError) as exc:
                fallidas.append({"fila": i, "motivo": str(exc)})

        if fallidas:
            return {"insertadas": 0, "usuarios_creados": 0, "fallidas": fallidas}

        creadas: list[tuple[int, int]] = []
        try:
            for payload in preparadas:
                gmail = payload.pop("gmail")
                unidad = self.registro_service.unidad_repo.create(payload)
                user = self._crear_o_reactivar_usuario(gmail, payload)
                # Ligar login → unidad para CU-O30 (find_by_usuario)
                self.registro_service.unidad_repo.update(
                    unidad["idunidademergencia"], {"idusuario": user["idusuario"]}
                )
                creadas.append((unidad["idunidademergencia"], user["idusuario"]))
                temp_password = secrets.token_urlsafe(12)
                self.credential_repo.create_temporary(user["idusuario"], temp_password)
                self.role_repo.assign_role_to_user(user["idusuario"], unidad_role["idrol"])
                self.notificacion.notify_invitacion(
                    cliente_id=idcliente,
                    user_id=user["idusuario"],
                    temp_password=temp_password,
                    actor_id=user_id,
                )
        except Exception as exc:  # noqa: BLE001 — todo-o-nada: compensar y reportar
            for unidad_id, uid in creadas:
                self.registro_service.unidad_repo.update(unidad_id, {"activo": False})
                self.user_repo.update(uid, {"activo": False})
            return {
                "insertadas": 0,
                "usuarios_creados": 0,
                "fallidas": [{"fila": 0, "motivo": f"Fallo al crear credenciales: {exc}"}],
            }

        n = len(preparadas)
        return {"insertadas": n, "usuarios_creados": n, "fallidas": []}

    def _crear_o_reactivar_usuario(self, gmail: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Reusa usuario inactivo (p. ej. compensación de lote fallido) para no bloquear gmail."""
        existing = self.user_repo.find_by_gmail(gmail)
        nombres = payload.get("unidademergencia", "Unidad")
        apellidos = payload.get("placa", "")
        if existing and not existing.get("activo", True):
            reactivated = self.user_repo.update(
                existing["idusuario"],
                {"nombres": nombres, "apellidos": apellidos, "activo": True},
            )
            assert reactivated is not None
            return reactivated
        return self.user_repo.create(
            {
                "nombres": nombres,
                "apellidos": apellidos,
                "gmail": gmail,
                "activo": True,
            }
        )
