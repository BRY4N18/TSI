"""CU-O33 — asignación manual de unidad."""

from __future__ import annotations

from typing import Any

from apps.accidentes.domain_constants import (
    ESTADO_ASIGNADO,
    ESTADO_BUSCANDO_UNIDAD,
    ESTADO_REPORTADO,
)
from apps.despacho.services.asignacion_inteligente_service import (
    AsignacionInteligenteService,
)
from core.repositories.accidentes.accidente_repository import AccidenteRepository
from core.repositories.accidentes.estado_accidente_repository import (
    EstadoAccidenteRepository,
)
from core.repositories.despacho.despacho_repository import DespachoRepository
from core.repositories.despacho.historial_estado_unidad_repository import (
    ESTADO_ACTIVA,
    HistorialEstadoUnidadRepository,
)


class AsignacionManualService:
    def __init__(
        self,
        asignacion: AsignacionInteligenteService | None = None,
        accidente_repo: AccidenteRepository | None = None,
        estado_repo: EstadoAccidenteRepository | None = None,
        despacho_repo: DespachoRepository | None = None,
        historial_unidad_repo: HistorialEstadoUnidadRepository | None = None,
    ):
        self.asignacion = asignacion or AsignacionInteligenteService()
        self.accidentes = accidente_repo or AccidenteRepository()
        self.estado = estado_repo or EstadoAccidenteRepository()
        self.despachos = despacho_repo or DespachoRepository()
        self.historial_unidad = historial_unidad_repo or HistorialEstadoUnidadRepository()

    def asignar(
        self,
        *,
        idaccidente: str,
        idunidademergencia: int,
        idusuario: int,
    ) -> dict[str, Any]:
        self._validar_elegible(idaccidente)
        if self.despachos.has_active_for_unidad(idunidademergencia):
            raise ValueError("Unidad no disponible")
        estado_unidad, _ = self.historial_unidad.get_current_estado(idunidademergencia)
        if estado_unidad != ESTADO_ACTIVA:
            raise ValueError("Unidad no disponible")
        activos = self.despachos.list_by_accidente(idaccidente, activo=True)
        if any(int(d["idunidademergencia"]) == idunidademergencia for d in activos):
            raise ValueError("Unidad ya asignada al caso")
        result = self.asignacion.ejecutar(
            idaccidente=idaccidente,
            idusuario=idusuario,
            idorigendespacho="Manual",
            idunidademergencia=idunidademergencia,
        )
        if result is None:
            raise ValueError("No se pudo crear despacho")
        estado_caso = self.estado.get_current_estado(idaccidente)
        return {
            "message": "Despacho manual creado",
            **result,
            "origen": "Manual",
            "estado_caso": estado_caso or ESTADO_BUSCANDO_UNIDAD,
        }

    def _validar_elegible(self, idaccidente: str) -> None:
        if not self.accidentes.find_by_id(idaccidente):
            raise LookupError("Accidente no encontrado")
        estado = self.estado.get_current_estado(idaccidente)
        if estado not in (ESTADO_REPORTADO, ESTADO_BUSCANDO_UNIDAD, ESTADO_ASIGNADO, None):
            raise ValueError("Caso no elegible para despacho")
