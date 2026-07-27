"""Consulta de suscripción propia + evaluación de acceso."""

from __future__ import annotations

from typing import Any

from core.repositories.suscripciones.suscripcion_repository import SuscripcionRepository
from apps.suscripciones.services.evaluacion_acceso_service import EvaluacionAccesoService


class ConsultaSuscripcionService:
    def __init__(
        self,
        suscripciones: SuscripcionRepository | None = None,
        acceso: EvaluacionAccesoService | None = None,
    ):
        self.suscripciones = suscripciones or SuscripcionRepository()
        self.acceso = acceso or EvaluacionAccesoService()

    def mi_suscripcion(self, idcliente: int) -> dict[str, Any] | None:
        return self.suscripciones.find_activa_by_cliente(idcliente)

    def acceso_permitido(self, idcliente: int) -> bool:
        sus = self.suscripciones.find_activa_by_cliente(idcliente)
        if not sus:
            # Cancelada con activo=false aún puede tener acceso hasta fecha_fin
            rows = list(self.suscripciones.pinot.query("SELECT * FROM Fact_Suscripcion", {}) or [])
            candidatos = [r for r in rows if r.get("idcliente") == idcliente]
            candidatos.sort(key=lambda r: r.get("id_suscripcion", 0), reverse=True)
            sus = candidatos[0] if candidatos else None
        return self.acceso.acceso_permitido(sus)
