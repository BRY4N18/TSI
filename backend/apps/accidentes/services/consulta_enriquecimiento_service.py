"""Consulta consolidada de enriquecimiento CU-O46."""

from __future__ import annotations

from typing import Any

from apps.accidentes.services.enriquecimiento_conductor_service import (
    EnriquecimientoConductorService,
)
from apps.accidentes.services.enriquecimiento_elemento_fisico_service import (
    EnriquecimientoElementoFisicoService,
)
from apps.accidentes.services.enriquecimiento_implicado_service import (
    EnriquecimientoImplicadoService,
)
from core.repositories.accidentes.elemento_climatico_repository import (
    ElementoClimaticoRepository,
)
from core.repositories.evidencia.accidente_read_repository import AccidenteReadRepository


class ConsultaEnriquecimientoService:
    def __init__(
        self,
        accidente_repo: AccidenteReadRepository | None = None,
        climatico_repo: ElementoClimaticoRepository | None = None,
        fisico_service: EnriquecimientoElementoFisicoService | None = None,
        conductor_service: EnriquecimientoConductorService | None = None,
        implicado_service: EnriquecimientoImplicadoService | None = None,
    ):
        self.accidente_repo = accidente_repo or AccidenteReadRepository()
        self.climatico_repo = climatico_repo or ElementoClimaticoRepository()
        self.fisico_service = fisico_service or EnriquecimientoElementoFisicoService()
        self.conductor_service = conductor_service or EnriquecimientoConductorService()
        self.implicado_service = implicado_service or EnriquecimientoImplicadoService()

    def obtener(self, idaccidente: str, *, idusuario: int | None = None) -> dict[str, Any]:
        if not self.accidente_repo.find_by_id(idaccidente):
            raise LookupError("Accidente no encontrado")
        return {
            "idaccidente": idaccidente,
            "clima": self.climatico_repo.find_activo_by_accidente(idaccidente),
            "elementos_fisicos": self.fisico_service.listar(idaccidente),
            "conductores": self.conductor_service.listar(
                idaccidente, idusuario=idusuario
            ),
            "implicados": self.implicado_service.listar(
                idaccidente, idusuario=idusuario
            ),
        }
