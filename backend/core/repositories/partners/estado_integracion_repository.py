"""Dim_EstadoIntegracion — catalogo de la foto congelada por llamada (RF-APM-005).

Que guarda este catalogo
------------------------
NO es el estado actual del partner. Es el valor que
`Fact_APIIntegracion.idestadointegracion` congela en cada llamada atendida:
en que estado estaba el partner en ese instante (RN-APM-006). La fuente de
verdad del estado actual es `Dim_Partner.activo` mas el entorno vigente de la
credencial.

Solo hay DOS estados alcanzables
--------------------------------
`Suspendido` (id 3) quedo desactivado el 2026-08-09 porque es inalcanzable: un
partner suspendido recibe 403 y su llamada no genera fila, igual que un 429
tampoco la genera (spec § 15 D2). Los dos que quedan se corresponden 1:1 con el
entorno de la credencial, redundancia aceptada y documentada en
`decisiones-pendientes.md` #22.
"""

from __future__ import annotations

from typing import Any

from core.pinot.client import PinotClient

ESTADO_PRUEBAS_ACTIVO = 1
ESTADO_PRODUCCION_ACTIVA = 2
# Sembrado pero inactivo: ninguna llamada atendida puede llevarlo.
ESTADO_SUSPENDIDO_INALCANZABLE = 3

ENTORNO_SANDBOX = "Sandbox"
ENTORNO_PRODUCCION = "Producción"

_ESTADO_POR_ENTORNO = {
    ENTORNO_SANDBOX: ESTADO_PRUEBAS_ACTIVO,
    ENTORNO_PRODUCCION: ESTADO_PRODUCCION_ACTIVA,
}


class EstadoIntegracionError(Exception):
    """El entorno recibido no tiene estado de catalogo asociado."""


class EstadoIntegracionRepository:
    """SOLO LECTURA. El catalogo lo siembra `database/seed_estado_integracion.py`;
    este modulo no lo escribe en runtime."""

    def __init__(self, pinot: PinotClient | None = None):
        self.pinot = pinot or PinotClient()

    def listar(self, *, solo_activos: bool = True) -> list[dict[str, Any]]:
        """El catalogo completo. `LIMIT` explicito: Pinot aplica 10 en silencio."""
        filas = self.pinot.query(
            "SELECT idestadointegracion, nombre, descripcion, activo "
            "FROM Dim_EstadoIntegracion LIMIT 100",
            {},
        )
        if solo_activos:
            filas = [f for f in filas if f.get("activo", True)]
        return sorted(filas, key=lambda f: int(f["idestadointegracion"]))

    def find_by_id(self, idestado: int) -> dict[str, Any] | None:
        filas = self.pinot.query(
            "SELECT idestadointegracion, nombre, descripcion, activo "
            "FROM Dim_EstadoIntegracion WHERE idestadointegracion = %(id)s LIMIT 1",
            {"id": idestado},
        )
        return filas[0] if filas else None

    @staticmethod
    def estado_para_entorno(entorno: str) -> int:
        """El estado que se congela al atender una llamada en ese entorno.

        Se resuelve del entorno y no del estado derivado del partner porque son
        los unicos dos valores que una llamada ATENDIDA puede tener: si el
        partner estuviera suspendido, la peticion no habria llegado hasta aqui.
        """
        estado = _ESTADO_POR_ENTORNO.get(entorno)
        if estado is None:
            raise EstadoIntegracionError(
                f"Entorno sin estado de catalogo: {entorno!r}. "
                f"Esperado uno de {sorted(_ESTADO_POR_ENTORNO)}"
            )
        return estado
