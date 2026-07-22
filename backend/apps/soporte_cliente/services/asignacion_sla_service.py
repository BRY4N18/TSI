"""RF-TIC-001 paso 4 y RF-TIC-005 paso 5 — asignación/renovación de SLA.

research.md Decision 5: `idplan` se resuelve desde la suscripción activa del
cliente (`Fact_Suscripcion`), no desde `Dim_Cliente.plan_suscripcion`.
research.md Decision 8 (clarificación Session 2026-07-21): la reapertura
reutiliza este mismo servicio para renovar el SLA contra la configuración
vigente actual.
"""

from __future__ import annotations

from datetime import datetime, timezone

from apps.soporte_cliente.domain_constants import SLA_EN_CURSO
from core.repositories.soporte.sla_config_repository import SLAConfigRepository
from core.repositories.soporte.suscripcion_repository import SuscripcionRepository


class AsignacionSLAService:
    def __init__(
        self,
        sla_config_repo: SLAConfigRepository | None = None,
        suscripcion_repo: SuscripcionRepository | None = None,
    ):
        self.sla_config_repo = sla_config_repo or SLAConfigRepository()
        self.suscripcion_repo = suscripcion_repo or SuscripcionRepository()

    def asignar(
        self, *, idcliente: int, tipo_incidencia: str, prioridad: str
    ) -> dict[str, object] | None:
        """Devuelve los campos de SLA a aplicar en Fact_Reclamo, o None si no hay regla vigente."""
        idplan = self.suscripcion_repo.find_idplan_activo(idcliente)
        if idplan is None:
            return None
        regla = self.sla_config_repo.find_vigente(
            idplan=idplan, tipoincidencia=tipo_incidencia, prioridad=prioridad
        )
        if not regla:
            return None
        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        return {
            "idslaconfig": regla["idslaconfig"],
            "sla_primera_respuesta": now_ms + int(regla["tiemporespuestamax"]) * 1000,
            "sla_resolucion": now_ms + int(regla["tiemporesolucionmax"]) * 1000,
            "sla_status": SLA_EN_CURSO,
        }
