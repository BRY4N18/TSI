"""RF-PAC-005 y RF-PAC-006 — reactivacion con cascada inversa SELECTIVA (CU-O55).

El servicio mas delicado de los tres modulos del departamento
--------------------------------------------------------------
Restituye **unicamente** las credenciales que estaban activas inmediatamente
antes de la suspension (RN-PAC-011). En concreto, **no reactiva las que el
partner revoco por seguridad**: resucitar una credencial comprometida seria un
fallo de seguridad grave, y es exactamente lo que esta regla previene.

Como lo consigue sin comprobar nada
------------------------------------
No pregunta "¿por que esta inactiva esta credencial?" — no podria: las tres
razones (cascada, revocacion, expiracion) son indistinguibles en
`Dim_CredencialAPI`. Lo que hace es leer las filas `desactivacion_por_cascada`
del ULTIMO evento de suspension y restituir **exactamente ese conjunto**.

Una credencial revocada por el partner ya estaba inactiva cuando llego la
suspension, asi que **no genero fila de cascada** y sencillamente no aparece en
la lista. La garantia es estructural: no hay ninguna condicion que un refactor
pueda borrar por descuido.

Y el sistema NUNCA reactiva solo
---------------------------------
No existe job, disparador ni rama automatica que llame aqui (RN-PAC-009). Aunque
el partner pague integramente su deuda, sigue suspendido hasta que un
Administrador lo reactive. No es un olvido: si aqui hubiera reactivacion
automatica chocaria con la de Suscripciones (RN-SUSF-011) y los dos estados
quedarian en contradiccion permanente (§ 15 D2).
"""

from __future__ import annotations

from typing import Any

from apps.partners.domain_constants import (
    CAMBIO_REACTIVACION,
    EJECUTADO_POR_ADMINISTRADOR,
    ESTADO_ACCESO_ACTIVO,
    ESTADO_ACCESO_SUSPENDIDO,
    SIN_SUSPENSION,
)
from apps.partners.services.denylist_credenciales import DenylistCredenciales
from core.repositories.partners.credencial_repository import CredencialRepository
from core.repositories.partners.historial_acceso_repository import (
    HistorialAccesoRepository,
)
from core.repositories.partners.partner_repository import PartnerRepository


class ReactivarPartnerError(Exception):
    def __init__(self, code: str, detail: str):
        self.code = code
        self.detail = detail
        super().__init__(detail)


class ReactivarPartnerService:
    def __init__(
        self,
        partners: PartnerRepository | None = None,
        credenciales: CredencialRepository | None = None,
        historial: HistorialAccesoRepository | None = None,
        denylist: DenylistCredenciales | None = None,
    ):
        self.partners = partners or PartnerRepository()
        self.credenciales = credenciales or CredencialRepository()
        self.historial = historial or HistorialAccesoRepository()
        self.denylist = denylist or DenylistCredenciales()

    def reactivar(self, *, idpartner: int, motivo: str = "") -> dict[str, Any]:
        """Reactiva al partner y restituye SOLO el conjunto de la cascada.

        El motivo es opcional aqui (a diferencia de la suspension): el SRS exige
        motivo al cortar el acceso, no al devolverlo.
        """
        partner = self.partners.find_by_id(int(idpartner))
        if not partner:
            raise ReactivarPartnerError("not_found", "Partner no encontrado")

        # Reactivar lo que nunca se suspendio es redundante: 409 y sin escribir.
        # Una entrada de `reactivacion` sin una suspension real que la respalde
        # falsearia la bitacora, que aqui no es solo auditoria.
        if partner.get("activo", False):
            raise ReactivarPartnerError(
                "partner_no_suspendido", "El partner no está suspendido"
            )

        a_restituir = self.historial.credenciales_de_la_ultima_cascada(int(idpartner))

        restituidas = 0
        for idcredencial in a_restituir:
            if self.credenciales.activar(int(idcredencial)) is not None:
                restituidas += 1

        # Simetrico a § 15 D4: si no se levantase la denegacion, el partner
        # reactivado seguiria rechazado hasta que caducase el TTL y la
        # reactivacion no seria tal durante ese minuto.
        self.denylist.retirar_varias(a_restituir)

        # Cuantas siguen inactivas: son las revocadas por seguridad y las
        # expiradas. Se expone a proposito, para que quede VISIBLE que no todas
        # vuelven — si alguien esperaba tres y ve dos, la respuesta ya se lo dijo.
        inactivas = [
            c
            for c in self.credenciales.list_by_partner(int(idpartner))
            if not c.get("activo", False)
        ]

        self.partners.update(
            int(idpartner),
            {
                "activo": True,
                # Centinelas, nunca NULL: Pinot no los almacena (RN-PAC-014).
                "fecha_suspension": SIN_SUSPENSION,
                "motivo_suspension": SIN_SUSPENSION,
            },
        )

        self.historial.registrar(
            idpartner=int(idpartner),
            tipo_cambio=CAMBIO_REACTIVACION,
            ejecutado_por=EJECUTADO_POR_ADMINISTRADOR,
            motivo=str(motivo or "").strip(),
            estado_anterior=ESTADO_ACCESO_SUSPENDIDO,
            estado_nuevo=ESTADO_ACCESO_ACTIVO,
        )

        return {
            "idpartner": int(idpartner),
            "activo": True,
            "credenciales_restituidas": restituidas,
            "credenciales_no_restituidas": len(inactivas),
        }
