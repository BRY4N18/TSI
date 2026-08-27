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
from core.repositories.red_operativa.suscripcion_activa_read_repository import (
    SuscripcionActivaReadRepository,
)

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
        suscripciones: SuscripcionActivaReadRepository | None = None,
    ):
        self.registro_service = registro_service or RegistroUnidadService()
        self.access = access or ProveedorAccessService()
        self.user_repo = user_repo or UserRepository()
        self.credential_repo = credential_repo or CredentialRepository()
        self.role_repo = role_repo or RoleRepository()
        self.notificacion = notificacion or OnboardingNotificacionService()
        self.suscripciones = suscripciones or SuscripcionActivaReadRepository()

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

        # RF-O40.6 / RF-O26.5 (2026-08-08): la carga en lote solo está
        # habilitada si el plan contratado (congelado en la suscripción
        # activa, no el plan en vivo — R-04 del SRS) la habilita.
        suscripcion = self.suscripciones.find_activa_by_cliente(idcliente)
        if not suscripcion or not suscripcion.get("carga_lote_habilitada"):
            raise PermissionError(
                "El plan contratado no habilita la carga en lote de unidades"
            )

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
                self._resolver_condado(payload)
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
                # Mismo criterio que el alta individual, incluida la excepción para el
                # rastro de un lote fallido y compensado.
                self.registro_service._validar_placa_libre(placa)
                if not self.registro_service.unidad_repo.condado_exists(payload["idcondado"]):
                    raise LookupError(f"idcondado {payload['idcondado']} no existe")

                placas_en_archivo.add(placa)
                gmails_en_archivo.add(gmail)
                preparadas.append({**payload, "gmail": gmail})
            except (KeyError, ValueError, LookupError) as exc:
                fallidas.append({"fila": i, "motivo": str(exc)})

        if fallidas:
            return {"insertadas": 0, "usuarios_creados": 0, "fallidas": fallidas}

        # Se guarda el registro completo, no solo el id: la compensación no puede
        # releer de Pinot lo que se acaba de escribir por Kafka (aún no está
        # ingerido), y `update()` sin `base` devuelve None en silencio cuando no
        # encuentra la fila — el rollback no haría nada y dejaría unidades activas
        # apuntando a un usuario que nunca llegó a existir.
        creadas: list[tuple[dict[str, Any], int]] = []
        try:
            for payload in preparadas:
                gmail = payload.pop("gmail")
                unidad = self.registro_service.unidad_repo.create(payload)
                user = self._crear_o_reactivar_usuario(gmail, payload)
                # Ligar login → unidad para CU-O30 (find_by_usuario)
                unidad = self.registro_service.unidad_repo.update(
                    unidad["idunidademergencia"],
                    {"idusuario": user["idusuario"]},
                    base=unidad,
                ) or unidad
                creadas.append((unidad, user["idusuario"]))
                temp_password = secrets.token_urlsafe(12)
                self.credential_repo.create_temporary(user["idusuario"], temp_password)
                self.role_repo.assign_role_to_user(user["idusuario"], unidad_role["idrol"])
                self.notificacion.notify_invitacion(
                    cliente_id=idcliente,
                    user_id=user["idusuario"],
                    temp_password=temp_password,
                    actor_id=user_id,
                    gmail=gmail,
                )
        except Exception as exc:  # noqa: BLE001 — todo-o-nada: compensar y reportar
            for unidad, uid in creadas:
                self.registro_service.unidad_repo.update(
                    int(unidad["idunidademergencia"]), {"activo": False}, base=unidad
                )
                self.user_repo.update(uid, {"activo": False})
            return {
                "insertadas": 0,
                "usuarios_creados": 0,
                "fallidas": [{"fila": 0, "motivo": f"Fallo al crear credenciales: {exc}"}],
            }

        n = len(preparadas)
        return {"insertadas": n, "usuarios_creados": n, "fallidas": []}

    def _resolver_condado(self, payload: dict[str, Any]) -> None:
        """Convierte `condado` (nombre) en `idcondado`, in-place.

        El CSV pedía `idcondado`: una clave interna que el proveedor de flota no
        tiene forma de conocer, y sin la cual el archivo entero era inservible
        (hallazgo #16). Ahora la columna del archivo es `condado`, con `estado`
        opcional para desambiguar los homónimos.

        Se conserva la compatibilidad con archivos viejos que traigan `idcondado`
        directamente: si ya viene, se respeta.
        """
        if payload.get("idcondado") not in (None, ""):
            # Puede venir como string desde el CSV.
            try:
                payload["idcondado"] = int(payload["idcondado"])
            except (TypeError, ValueError):
                raise KeyError("idcondado debe ser un número entero") from None
            payload.pop("condado", None)
            payload.pop("estado", None)
            return

        nombre_condado = str(payload.pop("condado", "") or "").strip()
        nombre_estado = str(payload.pop("estado", "") or "").strip()
        if not nombre_condado:
            raise KeyError("condado es requerido (nombre del condado, p. ej. 'Miami-Dade')")

        repo = self.registro_service.unidad_repo
        candidatos = repo.find_condados_por_nombre(nombre_condado)
        if not candidatos:
            raise LookupError(f"El condado '{nombre_condado}' no existe en el catálogo")

        if len(candidatos) > 1:
            if not nombre_estado:
                raise ValueError(
                    f"Hay más de un condado llamado '{nombre_condado}'. "
                    "Añada la columna 'estado' para indicar cuál."
                )
            estados = repo.find_estados_por_nombre(nombre_estado)
            if not estados:
                raise LookupError(f"El estado '{nombre_estado}' no existe en el catálogo")
            ids_estado = {int(e["idestado"]) for e in estados}
            candidatos = [c for c in candidatos if int(c["idestado"]) in ids_estado]
            if not candidatos:
                raise LookupError(
                    f"No hay un condado '{nombre_condado}' dentro del estado '{nombre_estado}'"
                )
            if len(candidatos) > 1:
                raise ValueError(
                    f"'{nombre_condado}' sigue siendo ambiguo dentro de '{nombre_estado}'"
                )

        payload["idcondado"] = int(candidatos[0]["idcondado"])

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
