"""Transiciones de caso para despacho — BUSCANDO_UNIDAD / ASIGNADO."""

from __future__ import annotations

from typing import Any

from apps.accidentes.domain_constants import (
    ESTADO_ASIGNADO,
    ESTADO_BUSCANDO_UNIDAD,
    ESTADO_REPORTADO,
)
from core.repositories.accidentes.estado_accidente_repository import EstadoAccidenteRepository


class EstadoAccidenteDespachoRepository:
    def __init__(self, estado_repo: EstadoAccidenteRepository | None = None):
        self.estado = estado_repo or EstadoAccidenteRepository()

    def publish_buscando_unidad_if_first(
        self, *, idaccidente: str, idusuario: int
    ) -> dict[str, Any] | None:
        current = self.estado.get_current_estado(idaccidente)
        if current in (ESTADO_BUSCANDO_UNIDAD, ESTADO_ASIGNADO):
            return None
        if current not in (ESTADO_REPORTADO, None):
            return None
        return self.estado.append_estado(
            idaccidente=idaccidente,
            estado=ESTADO_BUSCANDO_UNIDAD,
            idusuario=idusuario,
        )

    def publish_asignado_if_first_confirmed(
        self, *, idaccidente: str, idusuario: int
    ) -> dict[str, Any] | None:
        current = self.estado.get_current_estado(idaccidente)
        if current == ESTADO_ASIGNADO:
            return None
        return self.estado.append_estado(
            idaccidente=idaccidente,
            estado=ESTADO_ASIGNADO,
            idusuario=idusuario,
        )
