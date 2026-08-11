"""RF-PAC-001 y RF-PAC-002 — revocacion de autoservicio con reemplazo (CU-O55).

Es la respuesta a un incidente de seguridad, y eso decide TODO el diseno:

* **No espera aprobacion de nadie** (RN-PAC-001). Exigir que un Administrador
  autorice dejaria una credencial comprometida operando mientras alguien la
  revisa: el peor comportamiento posible ante una fuga (SRS L432).
* **No espera a la base.** Publicar en Kafka y confiar en Pinot dejaria la
  credencial sirviendo datos 5-15 s mas. Por eso se anade a la lista de
  denegacion en el mismo acto (`research.md` Decision 2).
* **No se puede ejecutar con una credencial de API**, solo con JWT. Si se
  pudiera, el atacante que ya tiene una credencial podria revocar las demas del
  partner: le estariamos dando la herramienta de sabotaje (Decision 1).
* **Entrega un reemplazo en el mismo acto** (RNF-PAC-004). El partner reacciona
  a un incidente; dejarlo sin acceso seria castigarlo por hacer lo correcto.

El orden de las operaciones no es intercambiable
------------------------------------------------
Se desactiva ANTES de emitir el reemplazo, y la unicidad del nombre se resuelve
EN MEMORIA. Si se releyera Pinot para comprobarla, veria la revocada todavia
activa y daria una colision falsa que **haria fallar la revocacion**, que es
justo la operacion que no puede fallar (Decision 4).
"""

from __future__ import annotations

from typing import Any

from apps.partners.domain_constants import (
    CAMBIO_REVOCACION_CREDENCIAL,
    EJECUTADO_POR_PARTNER,
    ESTADO_ACCESO_ACTIVO,
)
from apps.partners.services.denylist_credenciales import DenylistCredenciales
from apps.partners.services.emitir_credencial_service import EmitirCredencialService
from core.repositories.partners.credencial_repository import CredencialRepository
from core.repositories.partners.historial_acceso_repository import (
    HistorialAccesoRepository,
)


class RevocarCredencialError(Exception):
    def __init__(self, code: str, detail: str):
        self.code = code
        self.detail = detail
        super().__init__(detail)


class RevocarCredencialService:
    def __init__(
        self,
        credenciales: CredencialRepository | None = None,
        historial: HistorialAccesoRepository | None = None,
        emision: EmitirCredencialService | None = None,
        denylist: DenylistCredenciales | None = None,
    ):
        self.credenciales = credenciales or CredencialRepository()
        self.historial = historial or HistorialAccesoRepository()
        # RF-PAC-002 reutiliza la emision de #07 en vez de duplicarla: dos
        # generadores de secretos serian dos superficies de ataque, y la que
        # nadie mira acaba siendo la debil (`research.md` Decision 3).
        self.emision = emision or EmitirCredencialService()
        self.denylist = denylist or DenylistCredenciales()

    def revocar(
        self, *, idcredencial: int, idpartner_actor: int, motivo: str
    ) -> dict[str, Any]:
        """Revoca una credencial y devuelve la revocada + su reemplazo.

        `idpartner_actor` es el partner del token: la comprobacion de propiedad
        es parte del servicio, no de la vista, para que ningun endpoint futuro
        pueda saltarsela por descuido (RN-PAC-002).
        """
        motivo_limpio = str(motivo or "").strip()
        if not motivo_limpio:
            raise RevocarCredencialError(
                "validation_error", "motivo es obligatorio y no puede estar vacío"
            )

        credencial = self.credenciales.find_by_id(int(idcredencial))
        if not credencial:
            raise RevocarCredencialError("not_found", "Credencial no encontrada")

        # RN-PAC-002 — nadie revoca credenciales ajenas. 403, y sin escribir nada.
        if int(credencial["idpartner"]) != int(idpartner_actor):
            raise RevocarCredencialError(
                "propiedad_credencial", "La credencial no pertenece al partner autenticado"
            )

        # RN-PAC-003 — revocar lo ya revocado es redundante. 409 y sin escribir:
        # una segunda entrada de revocacion ensuciaria la bitacora, que es el
        # respaldo de RF-O55.4 y la fuente de la reactivacion selectiva.
        if not credencial.get("activo", False):
            raise RevocarCredencialError(
                "credencial_inactiva", "La credencial ya estaba inactiva"
            )

        self.credenciales.desactivar(int(idcredencial))

        # CIERRA LA VENTANA. A partir de aqui la credencial ya no sirve, aunque
        # Pinot tarde 15 s en enterarse (RNF-PAC-001).
        self.denylist.denegar(int(idcredencial))

        # RF-O55.1 exige el MISMO nombre. La unicidad excluye la recien revocada,
        # cuyo estado conocemos en memoria: releer Pinot daria colision falsa.
        reemplazo = self.emision.emitir(
            idpartner=int(credencial["idpartner"]),
            nombre_credencial=str(credencial["nombre_credencial"]),
            entorno=str(credencial["entorno"]),
            ejecutado_por=EJECUTADO_POR_PARTNER,
            excluir_de_unicidad=int(idcredencial),
        )

        # Revocar una credencial NO cambia el estado del partner: por eso
        # `estado_anterior` y `estado_nuevo` son iguales (data-model.md).
        self.historial.registrar(
            idpartner=int(credencial["idpartner"]),
            tipo_cambio=CAMBIO_REVOCACION_CREDENCIAL,
            ejecutado_por=EJECUTADO_POR_PARTNER,
            idcredencial=int(idcredencial),
            motivo=motivo_limpio,
            estado_anterior=ESTADO_ACCESO_ACTIVO,
            estado_nuevo=ESTADO_ACCESO_ACTIVO,
        )

        # RF-O55.2 — las demas siguen operando. Se cuentan para que la respuesta
        # lo haga visible: el partner acaba de tocar seguridad y necesita saber
        # que no se ha quedado sin servicio.
        intactas = [
            c
            for c in self.credenciales.list_by_partner(
                int(credencial["idpartner"]), solo_activas=True
            )
            if int(c["idcredencial"]) not in {int(idcredencial), int(reemplazo["idcredencial"])}
        ]

        return {
            "revocada": {
                "idcredencial": int(idcredencial),
                "nombre_credencial": credencial["nombre_credencial"],
                "entorno": credencial["entorno"],
                "activo": False,
            },
            # El secreto del reemplazo viaja SOLO aqui, una vez (RN-PON-005).
            "reemplazo": reemplazo,
            "credenciales_intactas": len(intactas),
        }
