"""RF-DES-010 — parámetros configurables del algoritmo."""

from __future__ import annotations

import logging
from typing import Any

from core.repositories.despacho.parametros_despacho_repository import (
    ParametrosDespachoRepository,
)

logger = logging.getLogger("tsi.despacho.parametros")

TIMEOUT_MIN = 30
TIMEOUT_MAX = 300


class ParametrosDespachoService:
    def __init__(self, repo: ParametrosDespachoRepository | None = None):
        self.repo = repo or ParametrosDespachoRepository()

    def obtener(self) -> dict[str, Any]:
        return self.repo.get()

    def actualizar(self, *, fields: dict[str, Any], idusuario: int) -> dict[str, Any]:
        self._validar(fields)
        updated = self.repo.publish_update(fields, idusuario=idusuario)
        logger.info("parámetros despacho actualizados por usuario %s", idusuario)
        return updated

    def _validar(self, fields: dict[str, Any]) -> None:
        if "timeout_respuesta_seg" in fields:
            timeout = int(fields["timeout_respuesta_seg"])
            if timeout < TIMEOUT_MIN or timeout > TIMEOUT_MAX:
                raise ValueError(
                    f"timeout_respuesta_seg debe estar entre {TIMEOUT_MIN} y {TIMEOUT_MAX}"
                )
        pesos = [
            fields.get("peso_distancia_pct"),
            fields.get("peso_concordancia_pct"),
            fields.get("peso_disponibilidad_pct"),
        ]
        if any(p is not None for p in pesos):
            current = self.repo.get()
            dist = int(fields.get("peso_distancia_pct", current["peso_distancia_pct"]))
            conc = int(fields.get("peso_concordancia_pct", current["peso_concordancia_pct"]))
            disp = int(fields.get("peso_disponibilidad_pct", current["peso_disponibilidad_pct"]))
            if dist + conc + disp != 100:
                raise ValueError("Los pesos deben sumar 100%")
