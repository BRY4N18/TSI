"""RF-PAC-004, RF-PAC-005 y RF-PAC-006 — suspension con cascada (CU-O55).

La cascada no es un efecto colateral: es lo que hace posible la reactivacion
------------------------------------------------------------------------------
Al suspender se desactivan **todas** las credenciales del partner, de pruebas y
de produccion, sin excepcion (RN-PAC-010), **y se inserta una fila de bitacora
por cada una** con su `idcredencial` (§ 15 D1).

Esa lista de filas ES la memoria de que estaba activo antes de la suspension.
Sin ella, al reactivar no habria forma de distinguir una credencial desactivada
por cascada de una que el partner revoco por estar comprometida, y la
reactivacion las resucitaria todas — el peor fallo posible de este modulo.

La propiedad que lo hace seguro: una credencial que **ya estaba inactiva** no
genera fila de cascada, asi que la reactivacion no la encuentra. La seguridad
sale POR CONSTRUCCION, no de una comprobacion aparte que alguien pueda olvidar.

Por que se desactiva fila por fila y no "logicamente"
-----------------------------------------------------
El middleware de #08 rechazaria igualmente las llamadas al ver el partner
suspendido. Aun asi se actualiza cada credencial: un partner suspendido con
credenciales `activo=true` es un **estado contradictorio** en la base, y quien
lo consulte por otra via sacara la conclusion equivocada (RN-PAC-012).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from apps.partners.domain_constants import (
    CAMBIO_DESACTIVACION_POR_CASCADA,
    CAMBIO_SUSPENSION_AUTOMATICA,
    CAMBIO_SUSPENSION_MANUAL,
    EJECUTADO_POR_ADMINISTRADOR,
    EJECUTADO_POR_SISTEMA,
    ESTADO_ACCESO_ACTIVO,
    ESTADO_ACCESO_SUSPENDIDO,
)
from apps.partners.services.denylist_credenciales import DenylistCredenciales
from apps.partners.services.partner_notificacion_service import (
    PartnerNotificacionService,
)
from core.repositories.partners.credencial_repository import CredencialRepository
from core.repositories.partners.historial_acceso_repository import (
    HistorialAccesoRepository,
)
from core.repositories.partners.partner_repository import PartnerRepository


class SuspenderPartnerError(Exception):
    def __init__(self, code: str, detail: str):
        self.code = code
        self.detail = detail
        super().__init__(detail)


class SuspenderPartnerService:
    def __init__(
        self,
        partners: PartnerRepository | None = None,
        credenciales: CredencialRepository | None = None,
        historial: HistorialAccesoRepository | None = None,
        denylist: DenylistCredenciales | None = None,
        notificacion: PartnerNotificacionService | None = None,
    ):
        self.partners = partners or PartnerRepository()
        self.credenciales = credenciales or CredencialRepository()
        self.historial = historial or HistorialAccesoRepository()
        self.denylist = denylist or DenylistCredenciales()
        self.notificacion = notificacion or PartnerNotificacionService()

    @staticmethod
    def _ahora_iso() -> str:
        # `Dim_Partner.fecha_suspension` es STRING en el esquema, no LONG.
        return datetime.now(timezone.utc).isoformat()

    def suspender(
        self,
        *,
        idpartner: int,
        motivo: str,
        automatica: bool,
    ) -> dict[str, Any]:
        """Suspende y ejecuta la cascada. `automatica` distingue mora de Admin.

        El motivo es obligatorio en ambos casos: la bitacora sin motivo no
        explica nada y RF-O55.4 lo exige.
        """
        motivo_limpio = str(motivo or "").strip()
        if not motivo_limpio:
            raise SuspenderPartnerError(
                "validation_error", "motivo es obligatorio y no puede estar vacío"
            )

        partner = self.partners.find_by_id(int(idpartner))
        if not partner:
            raise SuspenderPartnerError("not_found", "Partner no encontrado")

        if not partner.get("activo", False):
            raise SuspenderPartnerError(
                "partner_ya_suspendido", "El partner ya está suspendido"
            )

        # Lectura PREVIA: nada se ha escrito aun, asi que Pinot esta al dia y
        # este es el conjunto real de credenciales activas (Decision 5).
        activas = self.credenciales.list_by_partner(int(idpartner), solo_activas=True)

        for credencial in activas:
            idcredencial = int(credencial["idcredencial"])
            self.credenciales.desactivar(idcredencial)
            # UNA fila por credencial: esta es la lista que leera la reactivacion.
            self.historial.registrar(
                idpartner=int(idpartner),
                tipo_cambio=CAMBIO_DESACTIVACION_POR_CASCADA,
                ejecutado_por=EJECUTADO_POR_SISTEMA if automatica else EJECUTADO_POR_ADMINISTRADOR,
                idcredencial=idcredencial,
                motivo=motivo_limpio,
                estado_anterior=ESTADO_ACCESO_ACTIVO,
                estado_nuevo=ESTADO_ACCESO_SUSPENDIDO,
            )

        # § 15 D4 — el corte es inmediato tambien aqui. Sin esto, el partner
        # suspendido seguiria consumiendo 5-15 s con TODAS sus credenciales a la
        # vez: una fuga mayor que la que se cierra al revocar una sola.
        self.denylist.denegar_varias(int(c["idcredencial"]) for c in activas)

        self.partners.update(
            int(idpartner),
            {
                "activo": False,
                "fecha_suspension": self._ahora_iso(),
                "motivo_suspension": motivo_limpio,
            },
        )

        self.historial.registrar(
            idpartner=int(idpartner),
            tipo_cambio=(
                CAMBIO_SUSPENSION_AUTOMATICA if automatica else CAMBIO_SUSPENSION_MANUAL
            ),
            ejecutado_por=EJECUTADO_POR_SISTEMA if automatica else EJECUTADO_POR_ADMINISTRADOR,
            motivo=motivo_limpio,
            estado_anterior=ESTADO_ACCESO_ACTIVO,
            estado_nuevo=ESTADO_ACCESO_SUSPENDIDO,
        )

        # Al final y fail-open: el estado autoritativo ya esta escrito, y un
        # buzon caido no puede invalidar una suspension por mora ya ejecutada.
        self.notificacion.notificar_suspension(partner=partner, motivo=motivo_limpio)

        return {
            "idpartner": int(idpartner),
            "activo": False,
            "fecha_suspension": self._ahora_iso(),
            "motivo_suspension": motivo_limpio,
            "credenciales_desactivadas": len(activas),
        }
