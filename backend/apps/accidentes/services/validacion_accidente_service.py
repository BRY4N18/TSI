"""RF-REG-003 validation service."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from apps.accidentes.domain_constants import (
    DUPLICATE_WINDOW_MS,
    RETROSPECTIVE_WINDOW_MS,
)
from core.repositories.accidentes.accidente_repository import AccidenteRepository
from core.repositories.accidentes.estado_accidente_repository import (
    EstadoAccidenteRepository,
)
from core.repositories.accidentes.region_operativa_repository import (
    RegionOperativaRepository,
)


@dataclass
class ValidationResult:
    blocking_errors: list[dict[str, str]] = field(default_factory=list)
    advertencias: list[dict[str, str]] = field(default_factory=list)
    duplicate_candidates: list[dict[str, Any]] = field(default_factory=list)

    @property
    def is_blocked(self) -> bool:
        return bool(self.blocking_errors)

    @property
    def has_advertencias(self) -> bool:
        return bool(self.advertencias)


class ValidacionAccidenteService:
    def __init__(
        self,
        accidente_repo: AccidenteRepository | None = None,
        region_repo: RegionOperativaRepository | None = None,
        estado_repo: EstadoAccidenteRepository | None = None,
    ):
        self.accidente_repo = accidente_repo or AccidenteRepository()
        self.region_repo = region_repo or RegionOperativaRepository()
        self.estado_repo = estado_repo or EstadoAccidenteRepository()

    def validate_registro(self, data: dict[str, Any], *, now_ms: int | None = None) -> ValidationResult:
        import time

        result = ValidationResult()
        now_ms = now_ms or int(time.time() * 1000)

        lat = data.get("latitudinicio")
        lon = data.get("longitudinicio")
        if lat is None or lon is None:
            result.blocking_errors.append({"code": "campos_obligatorios", "detail": "GPS requerido"})
        elif not (-90 <= float(lat) <= 90 and -180 <= float(lon) <= 180):
            result.blocking_errors.append({"code": "gps_invalido", "detail": "Coordenadas fuera de rango global"})

        fechahora = data.get("fechahoraaccidente")
        if fechahora is not None:
            if fechahora > now_ms:
                result.blocking_errors.append({"code": "fecha_futura", "detail": "Fecha futura no permitida"})
            elif now_ms - fechahora > RETROSPECTIVE_WINDOW_MS:
                if not data.get("registroRetrospectivo") or not data.get("justificacionRetrospectiva"):
                    result.blocking_errors.append(
                        {"code": "retrospectivo_requerido", "detail": "Justificación retrospectiva requerida"}
                    )

        if not data.get("descripcion") or not data.get("idcalle"):
            result.blocking_errors.append({"code": "campos_obligatorios", "detail": "Campos obligatorios faltantes"})

        if result.is_blocked:
            return result

        idestado = self.region_repo.resolve_estado_from_calle(int(data["idcalle"]))
        if idestado is None or not self.region_repo.is_estado_en_produccion(idestado):
            result.advertencias.append({"code": "fuera_cobertura", "detail": "Fuera de cobertura operativa"})

        nearby = self.accidente_repo.find_nearby(
            latitud=float(lat),
            longitud=float(lon),
            fechahoraaccidente=int(fechahora),
            window_ms=DUPLICATE_WINDOW_MS,
        )
        if nearby:
            result.advertencias.append({"code": "duplicado_posible", "detail": "Posible duplicado detectado"})
            result.duplicate_candidates = nearby

        return result

    def suggest_parent_id(self, candidates: list[dict[str, Any]]) -> str | None:
        if not candidates:
            return None

        def primer_borrador_reportado_ts(candidate: dict[str, Any]) -> int:
            idaccidente = candidate.get("idaccidente")
            for entry in self.estado_repo.get_history(idaccidente):
                if entry.get("estado") in ("BORRADOR", "REPORTADO"):
                    return int(entry.get("fechahoramodificado", 0))
            return int(candidate.get("fechahoraaccidente", 0))

        return min(candidates, key=primer_borrador_reportado_ts).get("idaccidente")
