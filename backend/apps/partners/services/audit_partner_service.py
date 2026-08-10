"""Auditoria estructurada del onboarding de partners (RNF-PON-004).

Que registra
------------
Quien hizo que, sobre que partner y cuando: `idpartner`, `idusuario`,
timestamp y los campos modificados. Complementa la bitacora de negocio
(`Fact_HistorialAccesoPartner`, RF-PON-010) sin sustituirla: aquella es
estado consultable por el partner, esta es rastro de seguridad para el
operador.

Por que el saneado es activo y no una convencion
------------------------------------------------
«No registrar el secreto» escrito en un comentario se incumple el dia que
alguien pasa `**credencial` a un log por comodidad. Aqui `_sanear` **elimina**
cualquier clave sensible antes de emitir el registro, de forma recursiva. Es
la misma decision de diseno que `HistorialAccesoRepository`, que no expone
`update` en vez de pedir que nadie lo llame: la garantia esta en el codigo,
no en la disciplina de quien lo usa.

RN-PON-005 depende de esto: el secreto se entrega una sola vez y no debe ser
recuperable, y un log de auditoria es exactamente el sitio donde un secreto
sobrevive para siempre.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("tsi.partners.audit")

REDACTADO = "***"

# Se compara por subcadena, no por igualdad: cubre `client_secret`,
# `client_secret_hash`, `secreto`, `nuevo_password`... sin enumerarlos.
FRAGMENTOS_SENSIBLES = ("secret", "secreto", "password", "contrasena", "token", "hash")


class AuditPartnerService:
    """Rastro de seguridad por accion. Nunca lanza: auditar no puede romper el flujo."""

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    @classmethod
    def _es_sensible(cls, clave: Any) -> bool:
        return any(f in str(clave).lower() for f in FRAGMENTOS_SENSIBLES)

    @classmethod
    def _sanear(cls, valor: Any) -> Any:
        """Sustituye por `***` toda clave sensible, a cualquier profundidad."""
        if isinstance(valor, dict):
            return {
                k: (REDACTADO if cls._es_sensible(k) else cls._sanear(v))
                for k, v in valor.items()
            }
        if isinstance(valor, (list, tuple)):
            return [cls._sanear(v) for v in valor]
        return valor

    def registrar_accion(
        self,
        *,
        accion: str,
        idpartner: int | None,
        idusuario: int | None,
        campos: dict[str, Any] | None = None,
        resultado: str = "exito",
    ) -> dict[str, Any]:
        """Emite el registro y devuelve lo emitido (para poder verificarlo en test)."""
        entrada = {
            "accion": accion,
            "idpartner": idpartner,
            "idusuario": idusuario,
            "timestamp": self._now_iso(),
            "resultado": resultado,
            "campos": self._sanear(campos or {}),
        }
        logger.info("partner_audit", extra=entrada)
        return entrada

    # --- Atajos por caso de uso ----------------------------------------------

    def log_registro(self, *, idpartner: int, idusuario: int | None, campos: dict[str, Any]):
        return self.registrar_accion(
            accion="registro_partner", idpartner=idpartner, idusuario=idusuario, campos=campos
        )

    def log_asignacion_plan(
        self, *, idpartner: int, idusuario: int | None, plan: str, limite_mes: int
    ):
        return self.registrar_accion(
            accion="asignacion_plan",
            idpartner=idpartner,
            idusuario=idusuario,
            campos={"planapi": plan, "limitellamadasmes": limite_mes},
        )

    def log_emision_credencial(
        self, *, idpartner: int, idusuario: int | None, idcredencial: int,
        nombre_credencial: str, entorno: str,
    ):
        """Registra QUE credencial se emitio, jamas su secreto."""
        return self.registrar_accion(
            accion="emision_credencial",
            idpartner=idpartner,
            idusuario=idusuario,
            campos={
                "idcredencial": idcredencial,
                "nombre_credencial": nombre_credencial,
                "entorno": entorno,
            },
        )

    def log_promocion(
        self, *, idpartner: int, idusuario: int | None, decision: str, motivo: str = ""
    ):
        return self.registrar_accion(
            accion="resolucion_promocion",
            idpartner=idpartner,
            idusuario=idusuario,
            campos={"decision": decision, "motivo": motivo},
            resultado="exito" if decision == "aprobar" else "rechazado",
        )

    def log_denegacion(
        self, *, idpartner: int | None, idusuario: int | None, motivo: str
    ):
        """Un 403 es informacion de seguridad: quien intento operar sobre que."""
        return self.registrar_accion(
            accion="acceso_denegado",
            idpartner=idpartner,
            idusuario=idusuario,
            campos={"motivo": motivo},
            resultado="denegado",
        )
