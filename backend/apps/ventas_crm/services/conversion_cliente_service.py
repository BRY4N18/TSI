"""CU — conversión de prospecto a cliente (Ventas y CRM).

⚠️ **La conversión entrega credenciales.** Hasta 2026-08-26 este servicio creaba
el `Dim_Cliente` con `admin_local_id = None` y ahí terminaba: no creaba usuario,
no generaba contraseña temporal y no enviaba ningún correo. El prospecto pasaba
a cliente y no recibía nada con qué entrar — hallazgo #15 de la revisión del
24/08/2026 ("no llega el correo con las credenciales").

El camino correcto ya existía en `EntradaDirectaService` (CU-O96), que hace
exactamente esto para el alta directa. Aquí se replica tomando la identidad del
propio prospecto, que ya trae `nombres`, `apellidos` y `gmail` validados desde
`RegistrarProspectoService`.
"""

import logging
import secrets

from apps.cuentas_clientes.services.onboarding_notificacion_service import (
    OnboardingNotificacionService,
)
from apps.ventas_crm.domain import ConflictError, ForbiddenError, NotFoundError, ValidationError
from core.repositories.cuentas_clientes.cliente_repository import ClienteRepository
from core.repositories.cuentas_clientes.credential_repository import CredentialRepository
from core.repositories.cuentas_clientes.role_repository import RoleRepository
from core.repositories.cuentas_clientes.user_repository import UserRepository
from core.repositories.ventas_crm.pipeline_repository import PipelineRepository
from core.repositories.ventas_crm.prospecto_repository import ProspectoRepository

logger = logging.getLogger("tsi.ventas_crm.conversion")

TIPOS_CLIENTE_VALIDOS = {"Proveedor", "Aseguradora", "Municipio", "Smart City"}

CLIENTE_ROLE = "Cliente"


class ConversionClienteService:
    def __init__(
        self,
        prospectos=None,
        clientes=None,
        pipeline=None,
        users=None,
        credentials=None,
        roles=None,
        notificacion=None,
    ):
        self.prospectos = prospectos or ProspectoRepository()
        self.clientes = clientes or ClienteRepository()
        self.pipeline = pipeline or PipelineRepository()
        self.users = users or UserRepository()
        self.credentials = credentials or CredentialRepository()
        self.roles = roles or RoleRepository()
        self.notificacion = notificacion or OnboardingNotificacionService()

    def convertir(self, idprospecto, data, *, user_id, roles, idempotency_key):
        if not idempotency_key:
            raise ValidationError("Idempotency-Key es requerido")
        p = self.prospectos.find_by_id(idprospecto)
        if not p:
            raise NotFoundError("Prospecto no encontrado")
        if user_id != p.get("idusuario") and "Administrador" not in roles:
            raise ForbiddenError("No es dueño del prospecto")
        if (
            not p.get("activo", True)
            or p["etapa_actual"] != "Negociación"
            or data.get("etapa_actual_esperada") != "Negociación"
        ):
            raise ConflictError("Conversión requiere Negociación activa")
        tipo = data.get("tipo")
        nit = data.get("nit_identificacion")
        if not tipo or not nit:
            raise ValidationError("tipo y nit_identificacion son requeridos")
        if tipo not in TIPOS_CLIENTE_VALIDOS:
            raise ValidationError(f"tipo inválido: {tipo}")
        if self.clientes.exists_by_nit_any(nit):
            raise ConflictError("NIT ya registrado")

        # El administrador local de la cuenta nueva es el propio contacto del
        # prospecto: es quien viene negociando y quien espera poder entrar.
        admin_local, temp_password = self._provisionar_admin_local(p)

        cliente = self.clientes.create(
            {
                "idprospecto": idprospecto,
                "nombre": f'{p["nombres"]} {p["apellidos"]}',
                "razon_social": p["empresa"],
                "tipo": tipo,
                "nit_identificacion": nit,
                "admin_local_id": admin_local["idusuario"] if admin_local else None,
                "estado": "Activo",
                "estado_onboarding": "Pendiente",
            }
        )
        updated = self.prospectos.update(
            idprospecto,
            {"etapa_actual": "Ganado", "activo": False, "motivo_inactividad": "convertido"},
        )
        transicion = self.pipeline.create(
            {
                "id_prospecto": idprospecto,
                "etapa_anterior": "Negociación",
                "etapa_nueva": "Ganado",
                "notas": None,
                "motivo_perdida": None,
                "gerente_id": user_id,
            }
        )

        # El envío se reporta en la respuesta, no se traga. Una cuenta creada
        # cuyo correo de bienvenida falló es una cuenta sin acceso: si nadie lo
        # ve, nadie la rescata. Mismo criterio que `RegistroUnidadService`.
        invitacion_enviada = False
        if admin_local and temp_password:
            invitacion_enviada = self.notificacion.notify_invitacion(
                cliente_id=cliente["idcliente"],
                user_id=admin_local["idusuario"],
                temp_password=temp_password,
                actor_id=user_id,
                gmail=admin_local.get("gmail"),
            )

        resultado = {
            "prospecto": updated,
            "cliente": cliente,
            "transicion": transicion,
            "invitacion_enviada": invitacion_enviada,
        }
        if admin_local and not invitacion_enviada:
            resultado["invitacion_error"] = (
                "No se pudo enviar el correo con las credenciales. "
                "Use «Reenviar invitación» desde la cuenta."
            )
        return resultado

    def _provisionar_admin_local(self, prospecto) -> tuple[dict | None, str | None]:
        """Crea (o reutiliza) el usuario del contacto y le emite clave temporal.

        Reutiliza el usuario si el gmail ya existe —el contacto pudo autorregistrarse
        antes de que Ventas cerrara el trato— y en ese caso **no** emite una clave
        nueva: pisarle la contraseña a alguien que ya entra sería peor que no
        avisarle.
        """
        gmail = str(prospecto.get("gmail") or "").strip().lower()
        if not gmail:
            # Un prospecto sin correo no debería existir (RegistrarProspectoService
            # lo exige), pero si aparece uno antiguo la conversión no se cae: se
            # crea la cuenta sin admin y queda para asignar a mano.
            logger.warning(
                "conversion_prospecto_sin_gmail",
                extra={"idprospecto": prospecto.get("idprospecto")},
            )
            return None, None

        existente = self.users.find_by_gmail(gmail)
        if existente:
            return existente, None

        user = self.users.create(
            {
                "nombres": str(prospecto.get("nombres") or "").strip(),
                "apellidos": str(prospecto.get("apellidos") or "").strip(),
                "gmail": gmail,
                "activo": True,
            }
        )
        temp_password = secrets.token_urlsafe(12)
        self.credentials.create_temporary(user["idusuario"], temp_password)
        cliente_role = self.roles.find_role_by_name(CLIENTE_ROLE)
        if cliente_role:
            self.roles.assign_role_to_user(user["idusuario"], cliente_role["idrol"])
        return user, temp_password
