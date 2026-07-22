"""Tipo de unidad vs severidad — RF-DES-004 / RF-DES-010."""

from __future__ import annotations

from core.repositories.despacho.parametros_despacho_repository import (
    ParametrosDespachoRepository,
)

TIPO_AMBULANCIA = "Ambulancia"
TIPO_GRUA = "Grua"
TIPO_PATRULLA = "Patrulla"


class ConcordanciaTipoService:
    def __init__(self, parametros_repo: ParametrosDespachoRepository | None = None):
        self.parametros = parametros_repo or ParametrosDespachoRepository()

    def score_tipo(
        self,
        *,
        idseveridad: int,
        tipounidademergencia: str,
        descripcion: str | None = None,
    ) -> float:
        params = self.parametros.get()
        orden = self._orden_para_severidad(params, idseveridad, descripcion)
        tipo = self._normalize_tipo(tipounidademergencia)
        if tipo in orden:
            rank = orden.index(tipo)
            return max(0.0, 1.0 - (rank * 0.25))
        return 0.25

    def _orden_para_severidad(
        self, params: dict, idseveridad: int, descripcion: str | None
    ) -> list[str]:
        for item in params.get("prioridades_por_severidad", []):
            if item.get("idseveridad") == idseveridad:
                return [self._normalize_tipo(t) for t in item.get("orden_tipos", [])]
        if idseveridad == 3 and descripcion:
            lowered = descripcion.lower()
            keywords = params.get("keywords_severidad_moderada", [])
            if any(k in lowered for k in keywords):
                return [TIPO_AMBULANCIA, TIPO_GRUA, TIPO_PATRULLA]
            return [TIPO_GRUA, TIPO_PATRULLA, TIPO_AMBULANCIA]
        return [TIPO_PATRULLA, TIPO_GRUA, TIPO_AMBULANCIA]

    @staticmethod
    def _normalize_tipo(tipo: str) -> str:
        normalized = tipo.strip()
        if normalized.lower().startswith("gr"):
            return TIPO_GRUA
        if normalized.lower().startswith("amb"):
            return TIPO_AMBULANCIA
        if normalized.lower().startswith("pat"):
            return TIPO_PATRULLA
        return normalized
