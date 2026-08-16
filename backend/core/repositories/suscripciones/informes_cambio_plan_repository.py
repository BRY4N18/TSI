"""Consulta de solicitudes de cambio de plan — L3 de OT07 / CU-O34.

Es una **bandeja de trabajo**: quien la abre va a resolver lo que ve. De ahi que
ordene **ascendente por fecha de solicitud** —lo que lleva mas tiempo esperando
va primero—, al reves que un listado de consulta.
"""

from __future__ import annotations

from typing import Any, Sequence

from core.informes.paginacion import ASC, CampoCursor, Cursor, Orden
from core.pinot.client import PinotClient

CURSOR_SOLICITUDES = Cursor(
    CampoCursor("fecha_solicitud"), CampoCursor("idsolicitud")
)
ORDEN_SOLICITUDES = ASC  # bandeja: la mas antigua es la mas urgente

ESTADOS_SOLICITUD = ("Pendiente", "Aprobada", "Rechazada")


class InformesCambioPlanRepository:
    """Solo lectura. Ningun metodo escribe ni publica en Kafka."""

    def __init__(self, pinot: PinotClient | None = None):
        self.pinot = pinot or PinotClient()

    def solicitudes(
        self,
        *,
        cursor: tuple[Any, ...] | None = None,
        limit: int = 50,
        orden: Orden = ORDEN_SOLICITUDES,
        cuenta: int | None = None,
        estado: str | None = None,
    ) -> list[dict[str, Any]]:
        condiciones: list[str] = []
        params: dict[str, Any] = {"limit": limit + 1}

        if cuenta is not None:
            condiciones.append("idcliente = %(cuenta)s")
            params["cuenta"] = cuenta
        if estado is not None:
            condiciones.append("estado = %(estado)s")
            params["estado"] = estado
        if cursor:
            condiciones.append(CURSOR_SOLICITUDES.clausula(orden))
            params.update(CURSOR_SOLICITUDES.params(cursor))

        sql = (
            "SELECT idsolicitud, idcliente, idplanactual, idplansolicitado, estado, "
            "motivo, idadminaprobador, motivo_rechazo, fecha_solicitud, "
            "fecha_resolucion FROM Fact_Solicitud_Cambio_Plan"
            f"{_where(condiciones)} "
            f"ORDER BY {CURSOR_SOLICITUDES.order_by(orden)} LIMIT %(limit)s"
        )
        return self.pinot.query(sql, params)

    def nombres_de_usuario(self, idusuarios: Sequence[int]) -> dict[int, str]:
        ids = sorted({i for i in idusuarios if i is not None})
        if not ids:
            return {}

        filas = self.pinot.query(
            "SELECT idusuario, nombres, apellidos FROM Dim_Usuarios "
            "WHERE idusuario IN %(ids)s LIMIT %(limit)s",
            {"ids": ids, "limit": len(ids)},
        )
        return {
            f["idusuario"]: " ".join(
                p for p in (f.get("nombres"), f.get("apellidos")) if p
            ).strip()
            for f in filas
        }


def _where(condiciones: Sequence[str]) -> str:
    return f" WHERE {' AND '.join(condiciones)}" if condiciones else ""
