"""RF-EVI-004 — consulta de flota con estado derivado."""

from __future__ import annotations

from apps.despacho.services.disponibilidad_unidad_service import (
    DisponibilidadUnidadService,
)
from core.repositories.despacho.historial_estado_unidad_repository import (
    ESTADO_ACTIVA,
    HistorialEstadoUnidadRepository,
)
from core.repositories.despacho.unidad_emergencia_repository import (
    UnidadEmergenciaRepository,
)


class ConsultaFlotaService:
    def __init__(
        self,
        unidad_repo: UnidadEmergenciaRepository | None = None,
        historial_repo: HistorialEstadoUnidadRepository | None = None,
        disponibilidad: DisponibilidadUnidadService | None = None,
    ):
        self.unidad_repo = unidad_repo or UnidadEmergenciaRepository()
        self.historial_repo = historial_repo or HistorialEstadoUnidadRepository()
        self.disponibilidad = disponibilidad or DisponibilidadUnidadService(
            historial_repo=self.historial_repo,
            unidad_repo=self.unidad_repo,
        )

    def listar(
        self,
        *,
        estado: str | None = None,
        idtipounidad: int | None = None,
        limit: int = 20,
        cursor: int | None = None,
    ) -> tuple[list[dict], str | None]:
        unidades = self.unidad_repo.list_active(
            idtipounidad=idtipounidad,
            limit=limit + 1,
            cursor=cursor,
        )
        next_cursor = None
        if len(unidades) > limit:
            unidades = unidades[:limit]
            next_cursor = str(unidades[-1]["idunidademergencia"])

        items = []
        for unidad in unidades:
            uid = unidad["idunidademergencia"]
            estado_actual, _ = self.historial_repo.get_current_estado(uid)
            if estado and estado_actual != estado:
                continue
            items.append(
                {
                    "idunidademergencia": uid,
                    "nombre": unidad.get("unidademergencia") or unidad.get("nombre"),
                    "idtipounidad": unidad.get("idtipounidad"),
                    "estado_actual": estado_actual,
                    "incluido_en_despacho": estado_actual == ESTADO_ACTIVA,
                }
            )
        return items, next_cursor
