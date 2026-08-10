"""RF-PON-012 — consulta del estado de incorporacion (CU-O48, CU-O49).

El ESTADO NO ES UNA COLUMNA: se deriva de `Dim_Partner` (`activo`, `planapi`) y
del ultimo evento de la bitacora. `Dim_Partner.activo` es la unica fuente de
verdad del eje activo/suspendido (RN-PON-009).

Las credenciales NUNCA incluyen el secreto: solo se transmite una vez, en la
respuesta de creacion (RN-PON-005).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from apps.partners.domain_constants import (
    CAMBIO_ACTIVACION_PRODUCCION,
    CAMBIO_ACTIVACION_SANDBOX,
    CAMBIO_SOLICITUD_PRODUCCION,
    ENTORNO_PRODUCCION,
    ESTADO_PENDIENTE_APROBACION,
    ESTADO_PLAN_ASIGNADO,
    ESTADO_PRODUCCION_ACTIVA,
    ESTADO_PRUEBAS_ACTIVO,
    ESTADO_REGISTRADO,
    ESTADO_SUSPENDIDO,
    SIN_PLAN,
)
from core.repositories.partners.credencial_repository import CredencialRepository
from core.repositories.partners.historial_acceso_repository import (
    HistorialAccesoRepository,
)
from core.repositories.partners.partner_repository import PartnerRepository

# Campos que jamas salen en una respuesta de consulta.
_CAMPOS_SENSIBLES = frozenset({"client_secret_hash", "client_secret"})


def _sin_secreto(credencial: dict[str, Any]) -> dict[str, Any]:
    """Filtra el hash y cualquier resto de secreto antes de exponer."""
    return {k: v for k, v in credencial.items() if k not in _CAMPOS_SENSIBLES}


class ConsultaPartnerError(Exception):
    def __init__(self, code: str, detail: str):
        self.code = code
        self.detail = detail
        super().__init__(detail)


class ConsultaPartnerService:
    def __init__(
        self,
        partners: PartnerRepository | None = None,
        credenciales: CredencialRepository | None = None,
        historial: HistorialAccesoRepository | None = None,
    ):
        self.partners = partners or PartnerRepository()
        self.credenciales = credenciales or CredencialRepository()
        self.historial = historial or HistorialAccesoRepository()

    # --- Derivacion del estado ---------------------------------------------

    def derivar_estado(
        self,
        partner: dict[str, Any],
        credenciales: list[dict[str, Any]] | None = None,
        ultimo_evento: dict[str, Any] | None = None,
    ) -> str:
        """Estado derivado, en el orden de precedencia de `spec.md` seccion 9."""
        # Suspendido manda sobre todo: es el eje que gobierna `activo`.
        if not partner.get("activo", False):
            return ESTADO_SUSPENDIDO

        # Guarda contra el CENTINELA, no contra NULL: un partner sin plan lleva
        # cadena vacia. Comparar con `is not None` seria siempre cierto y
        # dejaria emitir credenciales sin plan (RF-PON-004).
        if str(partner.get("planapi", SIN_PLAN)) == SIN_PLAN:
            return ESTADO_REGISTRADO

        if ultimo_evento and ultimo_evento.get("tipo_cambio") == CAMBIO_SOLICITUD_PRODUCCION:
            return ESTADO_PENDIENTE_APROBACION

        creds = credenciales if credenciales is not None else []
        if any(
            c.get("entorno") == ENTORNO_PRODUCCION and c.get("activo") for c in creds
        ):
            return ESTADO_PRODUCCION_ACTIVA

        # "Pruebas activo" no exige credencial viva: una credencial vencida deja
        # al partner aqui, listo para regenerar sin repetir el alta (RN-PON-006).
        if creds or self._hubo_sandbox(partner):
            return ESTADO_PRUEBAS_ACTIVO

        return ESTADO_PLAN_ASIGNADO

    def _hubo_sandbox(self, partner: dict[str, Any]) -> bool:
        for ev in self.historial.list_by_partner(int(partner["idpartner"]), limit=200):
            if ev.get("tipo_cambio") in (
                CAMBIO_ACTIVACION_SANDBOX,
                CAMBIO_ACTIVACION_PRODUCCION,
            ):
                return True
        return False

    # --- Consultas ----------------------------------------------------------

    def detalle(self, idpartner: int) -> dict[str, Any]:
        partner = self.partners.find_by_id(idpartner)
        if not partner:
            raise ConsultaPartnerError("not_found", "Partner no encontrado")

        credenciales = self.credenciales.list_by_partner(idpartner)
        historial = self.historial.list_by_partner(idpartner)
        ultimo = historial[0] if historial else None

        return {
            **partner,
            "estado": self.derivar_estado(partner, credenciales, ultimo),
            "credenciales": [_sin_secreto(c) for c in credenciales],
            "historial": historial,
        }

    def listar(
        self, *, limit: int = 20, cursor: int | None = None, estado: str | None = None
    ) -> dict[str, Any]:
        filas, next_cursor = self.partners.list(limit=limit, cursor=cursor)
        items = []
        for p in filas:
            creds = self.credenciales.list_by_partner(int(p["idpartner"]))
            ultimo = self.historial.ultimo_evento(int(p["idpartner"]))
            item = {**p, "estado": self.derivar_estado(p, creds, ultimo)}
            if estado and item["estado"] != estado:
                continue
            items.append(item)
        return {"items": items, "next_cursor": next_cursor, "limit": limit}

    def credenciales_de(self, idpartner: int, **filtros: Any) -> list[dict[str, Any]]:
        return [_sin_secreto(c) for c in self.credenciales.list_by_partner(idpartner, **filtros)]

    @staticmethod
    def ahora_ms() -> int:
        return int(datetime.now(timezone.utc).timestamp() * 1000)
