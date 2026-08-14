"""CU-O54 — registrar unidad de emergencia individual (actor Proveedor).

`gmail` es opcional (SRS 3.5.1, RF-O39.5/RF-O39.6): si se envía, crea login
(rol Unidad), credencial temporal e invitación, y liga
`Dim_UnidadEmergencia.idusuario` (requisito para CU-O30). Si se omite, la
unidad queda en el catálogo sin acceso propio — no puede declarar
disponibilidad ni recibir despachos hasta que se le asigne login (edición
posterior o CU-O30 vía otro alta). Solo la carga en lote (CU-O40) exige
correo en cada fila.
Si SMTP falla, la unidad y el usuario se conservan; la respuesta reporta
`invitacion_enviada=false` + `invitacion_error` (nunca la contraseña).
"""

from __future__ import annotations

import re
import secrets
from typing import Any

from apps.cuentas_clientes.services.onboarding_notificacion_service import (
    OnboardingNotificacionService,
)
from apps.red_operativa.services.proveedor_access_service import (
    ProveedorAccessError,
    ProveedorAccessService,
)
from core.repositories.cuentas_clientes.credential_repository import CredentialRepository
from core.repositories.cuentas_clientes.role_repository import RoleRepository
from core.repositories.cuentas_clientes.user_repository import UserRepository
from core.repositories.red_operativa.baja_unidad_repository import BajaUnidadRepository
from core.repositories.red_operativa.unidad_emergencia_repository import (
    UnidadEmergenciaRepository,
)

TIPOS_PROPIEDAD = {"Propia", "Externa"}
TIPOS_UNIDAD = {"Ambulancia", "Grúa", "Patrulla", "Bomberos", "Defensa Civil"}
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
UNIDAD_ROLE = "Unidad"
SMTP_FAIL_MSG = "No se pudo enviar la invitación por correo. Use Reenviar."


class RegistroUnidadService:
    def __init__(
        self,
        unidad_repo: UnidadEmergenciaRepository | None = None,
        access: ProveedorAccessService | None = None,
        user_repo: UserRepository | None = None,
        credential_repo: CredentialRepository | None = None,
        role_repo: RoleRepository | None = None,
        notificacion: OnboardingNotificacionService | None = None,
        baja_repo: BajaUnidadRepository | None = None,
    ):
        self.baja_repo = baja_repo or BajaUnidadRepository()
        self.unidad_repo = unidad_repo or UnidadEmergenciaRepository()
        self.access = access or ProveedorAccessService()
        self.user_repo = user_repo or UserRepository()
        self.credential_repo = credential_repo or CredentialRepository()
        self.role_repo = role_repo or RoleRepository()
        self.notificacion = notificacion or OnboardingNotificacionService()

    def registrar(
        self,
        data: dict[str, Any],
        *,
        user_id: int,
        roles: list[str],
    ) -> dict[str, Any]:
        cliente = self.access.resolve_cliente_activo(user_id=user_id, roles=roles)
        payload = dict(data)
        payload.pop("idcliente", None)
        gmail_raw = payload.pop("gmail", None)
        payload["idcliente"] = int(cliente["idcliente"])
        if not payload.get("tipopropiedad"):
            payload["tipopropiedad"] = "Externa"
        self._validar(payload)
        self._validar_placa_libre(payload["placa"])
        if not self.unidad_repo.condado_exists(payload["idcondado"]):
            raise LookupError(f"idcondado {payload['idcondado']} no existe")

        tiene_gmail = gmail_raw is not None and str(gmail_raw).strip() != ""
        gmail: str | None = None
        unidad_role: dict[str, Any] | None = None
        if tiene_gmail:
            gmail = self._normalizar_gmail(gmail_raw)
            unidad_role = self.role_repo.find_role_by_name(UNIDAD_ROLE)
            if not unidad_role or not unidad_role.get("activo", True):
                raise ValueError(f"Rol '{UNIDAD_ROLE}' no configurado o inactivo")
            existing_user = self.user_repo.find_by_gmail(gmail)
            if existing_user and existing_user.get("activo", True):
                raise ValueError(f"Correo ya registrado: {gmail}")

        unidad = self.unidad_repo.create(payload)

        if not tiene_gmail:
            unidad["usuario_creado"] = False
            unidad["invitacion_enviada"] = False
            return unidad

        assert gmail is not None and unidad_role is not None
        user = self._crear_o_reactivar_usuario(gmail, payload)
        # Pass local create payload as base — avoid Pinot read-after-write lag
        # which can return incomplete rows (missing idcondado / idcliente=0).
        updated = self.unidad_repo.update(
            unidad["idunidademergencia"],
            {"idusuario": user["idusuario"]},
            base=unidad,
        )
        temp_password = secrets.token_urlsafe(12)
        self.credential_repo.create_temporary(user["idusuario"], temp_password)
        self.role_repo.assign_role_to_user(user["idusuario"], unidad_role["idrol"])
        enviada = self.notificacion.notify_invitacion(
            cliente_id=cliente["idcliente"],
            user_id=user["idusuario"],
            temp_password=temp_password,
            actor_id=user_id,
            gmail=gmail,
        )
        result = updated or unidad
        result["idusuario"] = user["idusuario"]
        result["usuario_creado"] = True
        result["invitacion_enviada"] = bool(enviada)
        if not enviada:
            result["invitacion_error"] = SMTP_FAIL_MSG
        else:
            result.pop("invitacion_error", None)
        # Never expose credentials in API responses
        result.pop("temp_password", None)
        result.pop("password", None)
        return result

    def _normalizar_gmail(self, gmail_raw: Any) -> str:
        gmail = str(gmail_raw).strip().lower()
        if not gmail or not EMAIL_RE.match(gmail):
            raise KeyError("gmail invalido")
        return gmail

    def _crear_o_reactivar_usuario(self, gmail: str, payload: dict[str, Any]) -> dict[str, Any]:
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

    def _validar_placa_libre(self, placa: str) -> None:
        """La placa es el identificador único de negocio (SRS §3.5.1).

        No basta con mirar entre las unidades activas: una unidad **dada de baja**
        conserva su placa y el SRS permite reactivarla, así que dejar registrar otra
        con esa misma placa acababa en dos unidades activas con la misma.

        Sí se admite reutilizar la placa de una unidad inactiva **sin baja
        registrada**: eso no es una baja de negocio sino el rastro de una carga en
        lote que falló y se compensó desactivando lo ya insertado. Bloquearla dejaría
        el reintento del lote permanentemente roto, y toda baja real registra su
        motivo y su tipo en `Fact_BajaUnidad`, así que la distinción es fiable.
        """
        existente = self.unidad_repo.find_by_placa(placa)
        if not existente:
            return
        if existente.get("activo"):
            raise ValueError(f"Ya existe una unidad con placa {placa}")
        if self.baja_repo.list_by_unidad(int(existente["idunidademergencia"])):
            raise ValueError(
                f"La placa {placa} pertenece a una unidad dada de baja. "
                "Reactívala en vez de registrar una nueva."
            )

    def _validar(self, data: dict[str, Any]) -> None:
        if not data.get("idcliente"):
            raise KeyError("idcliente es requerido")
        if data.get("tipopropiedad") not in TIPOS_PROPIEDAD:
            raise KeyError("tipopropiedad inválido")
        if not data.get("placa"):
            raise KeyError("placa es requerida")
        if not data.get("idcondado"):
            raise KeyError("idcondado es requerido")
        if not data.get("unidademergencia"):
            raise KeyError("unidademergencia es requerido")
        if data.get("tipounidademergencia") not in TIPOS_UNIDAD:
            raise KeyError("tipounidademergencia inválido")
        if data["tipopropiedad"] == "Externa" and not data.get("contactoproveedor"):
            raise KeyError("contactoproveedor es requerido para unidades Externa")
