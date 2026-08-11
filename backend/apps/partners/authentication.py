"""Autenticacion por credencial de API para `/datos/*` (RF-APM-001).

Esta es la puerta de la API que consume el partner, y NO es la misma que la de
las pantallas: un JWT humano no autentica aqui, y una credencial de API no
autentica en las pantallas. Son dos mecanismos con dos poblaciones distintas.

El acceso exige TRES condiciones con tres duenos distintos
----------------------------------------------------------
Decision D2 de `partner-access-management`. Las tres son independientes por
origen y **se exigen todas**:

1. **Credencial valida** — existe, `activo=true` y no vencida. La invalida #09.
2. **Partner activo** — `Dim_Partner.activo`. Lo suspende #09 por mora de
   excedente de API.
3. **Suscripcion vigente** — `Fact_Suscripcion.estado`. La suspende
   `subscriptions-and-billing` por su propia mora.

La tercera se anadio el 2026-08-08 y cierra un hueco real: sin ella, un cliente
con la suscripcion suspendida seguia consumiendo la API.

La vigencia se deriva de los datos (`activo`, `fecha_expiracion < ahora`), no de
que un job la haya marcado: es fail-safe, no depende de que nada haya corrido.

Antes de las tres: la lista de denegacion
-----------------------------------------
Las tres condiciones se leen de Pinot, y Pinot va 5-15 s por detras de lo que se
acaba de escribir. Por eso lo PRIMERO que se comprueba es la lista de denegacion
en memoria que alimentan la revocacion y la suspension de #09: sin ella, una
credencial revocada hace dos segundos seguiria sirviendo datos. Ver
`services/denylist_credenciales.py` y § 15 D4 de aquel modulo.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from rest_framework import authentication, exceptions, permissions

from apps.partners.services.denylist_credenciales import DenylistCredenciales
from apps.partners.services.secreto_service import SecretoService
from core.pinot.client import PinotClient
from core.repositories.partners.plan_read_repository import PlanReadRepository

CABECERA_CLIENT_ID = "HTTP_X_CLIENT_ID"
CABECERA_CLIENT_SECRET = "HTTP_X_CLIENT_SECRET"


class PartnerAPIUser:
    """Identidad de una llamada de maquina. No es un usuario humano.

    DRF exige un objeto con `is_authenticated`; este lleva ademas el partner y
    la credencial resueltos, para que la vista no vuelva a consultarlos.
    """

    is_authenticated = True

    def __init__(self, partner: dict[str, Any], credencial: dict[str, Any]):
        self.partner = partner
        self.credencial = credencial
        self.idpartner = int(partner["idpartner"])
        self.idcliente = int(partner["idcliente"])
        self.idcredencial = int(credencial["idcredencial"])
        self.entorno = credencial["entorno"]
        # Un cliente de API no tiene roles humanos: que quede explicito para que
        # ningun permiso de pantalla lo acepte por accidente.
        self.roles: list[str] = []

    def __str__(self) -> str:
        return f"partner:{self.idpartner}/cred:{self.idcredencial}"


class CredencialAPIAuthentication(authentication.BaseAuthentication):
    """Resuelve `X-Client-Id` + `X-Client-Secret` contra `Dim_CredencialAPI`."""

    def __init__(
        self,
        pinot: PinotClient | None = None,
        secretos: SecretoService | None = None,
        planes: PlanReadRepository | None = None,
        denylist: DenylistCredenciales | None = None,
    ):
        self.pinot = pinot or PinotClient()
        self.secretos = secretos or SecretoService()
        self.planes = planes or PlanReadRepository(pinot=self.pinot)
        self.denylist = denylist or DenylistCredenciales()

    @staticmethod
    def _now_ms() -> int:
        return int(datetime.now(timezone.utc).timestamp() * 1000)

    def authenticate(self, request):
        client_id = request.META.get(CABECERA_CLIENT_ID)
        client_secret = request.META.get(CABECERA_CLIENT_SECRET)
        if not client_id or not client_secret:
            # Sin cabeceras no es "credencial invalida": es que esta peticion no
            # intenta autenticarse por este mecanismo. Se devuelve None para que
            # DRF responda 401 por ausencia de credenciales.
            return None

        # ORDEN CRITICO (T006, `research.md` Decision 2 de #09).
        #
        # La lista de denegacion se consulta ANTES que nada: antes de Pinot y,
        # sobre todo, antes de cualquier cache positiva que se anada aqui en el
        # futuro para aliviar el bcrypt. En el orden inverso, esa cache
        # *alargaria* la ventana de exposicion en vez de cerrarla — una
        # optimizacion de rendimiento convertida en agujero de seguridad.
        #
        # Se resuelve sobre el `client_id` de la peticion, sin tocar la base:
        # justamente porque Pinot todavia no sabe que la credencial fue revocada.
        ids = self._descomponer_client_id(str(client_id))
        if ids is not None and self.denylist.contiene(ids[1]):
            raise exceptions.AuthenticationFailed("La credencial fue revocada o suspendida")

        credencial = self._buscar_credencial(str(client_id))
        if credencial is None:
            raise exceptions.AuthenticationFailed("Credencial de API inválida")

        if not credencial.get("activo", False):
            raise exceptions.AuthenticationFailed("La credencial fue revocada o suspendida")

        if int(credencial.get("fecha_expiracion", 0)) < self._now_ms():
            raise exceptions.AuthenticationFailed("La credencial está vencida")

        if not self.secretos.verificar(
            str(client_secret), str(credencial.get("client_secret_hash", ""))
        ):
            raise exceptions.AuthenticationFailed("Credencial de API inválida")

        partner = self._buscar_partner(int(credencial["idpartner"]))
        if partner is None:
            raise exceptions.AuthenticationFailed("El partner de la credencial no existe")

        return PartnerAPIUser(partner, credencial), None

    def authenticate_header(self, request) -> str:
        """Sin esto DRF devuelve 403 en vez de 401 cuando faltan credenciales."""
        return "X-Client-Id"

    # --- Consultas -----------------------------------------------------------

    def _buscar_credencial(self, client_id: str) -> dict[str, Any] | None:
        """El `client_id` codifica partner y credencial: `tsi-p{id}-c{id}`."""
        ids = self._descomponer_client_id(client_id)
        if ids is None:
            return None
        _idpartner, idcredencial = ids
        filas = self.pinot.query(
            "SELECT * FROM Dim_CredencialAPI WHERE idcredencial = %(id)s LIMIT 1",
            {"id": idcredencial},
        )
        return filas[0] if filas else None

    @staticmethod
    def _descomponer_client_id(client_id: str) -> tuple[int, int] | None:
        """`tsi-p12-c88` -> (12, 88). Devuelve None si no tiene esa forma."""
        partes = client_id.split("-")
        if len(partes) != 3 or partes[0] != "tsi":
            return None
        if not partes[1].startswith("p") or not partes[2].startswith("c"):
            return None
        try:
            return int(partes[1][1:]), int(partes[2][1:])
        except ValueError:
            return None

    def _buscar_partner(self, idpartner: int) -> dict[str, Any] | None:
        filas = self.pinot.query(
            "SELECT * FROM Dim_Partner WHERE idpartner = %(id)s LIMIT 1", {"id": idpartner}
        )
        return filas[0] if filas else None


class PartnerHabilitado(permissions.BasePermission):
    """Condiciones 2 y 3: partner activo **y** suscripcion vigente (T024b).

    Van aqui y no en `authenticate()` porque son **autorizacion, no identidad**:
    la credencial es valida y sabemos quien llama; lo que falla es su derecho a
    consumir. El spec pide 403 para ambas, y DRF solo devuelve 403 desde un
    permiso — desde la autenticacion saldria 401.

    Las dos suspensiones tienen duenos distintos y son independientes: el
    partner lo suspende #09 por mora de excedente, y la suscripcion la suspende
    `subscriptions-and-billing` por la suya. El acceso exige las dos.
    """

    MENSAJE_PARTNER = "El partner está suspendido"
    MENSAJE_SUSCRIPCION = "El cliente no tiene una suscripción vigente"

    def __init__(self, planes: PlanReadRepository | None = None):
        self._planes = planes

    def _plan_read(self) -> PlanReadRepository:
        if self._planes is None:
            self._planes = PlanReadRepository()
        return self._planes

    def has_permission(self, request, view) -> bool:
        usuario = getattr(request, "user", None)
        if not isinstance(usuario, PartnerAPIUser):
            return False

        if not usuario.partner.get("activo", False):
            self.message = self.MENSAJE_PARTNER
            return False

        # Sin suscripcion vigente no hay derecho a consumir, aunque la
        # credencial y el partner esten perfectos. Este era el hueco.
        if self._plan_read().suscripcion_vigente(usuario.idcliente) is None:
            self.message = self.MENSAJE_SUSCRIPCION
            return False

        return True
