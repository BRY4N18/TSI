"""Consultas de versiones del contrato y alcance de datos — L4 y L5.

Las versiones retiradas SE INCLUYEN (FR-004)
---------------------------------------------
Una version retirada es informacion util: dice desde cuando dejo de soportarse,
que es lo que un partner necesita para saber si su integracion sigue viva. El
listado la muestra con su fecha de retiro.

⚠️ Un cliente sin alcance configurado NO tiene acceso ilimitado (FR-023)
-------------------------------------------------------------------------
`Dim_Preferencias_Cliente.zonas_geograficas` ausente significa **que no se ha
configurado**, no «todas las zonas». Presentar la ausencia como lista vacia e
interpretarla como «sin restriccion» daria por contratado un alcance que nadie
acordo — y en un modulo cuya funcion es decir que datos puede consumir un
partner, eso es una fuga de alcance.
"""

from __future__ import annotations

from typing import Any, Sequence

from core.informes.paginacion import DESC, CampoCursor, Cursor, Orden
from core.pinot.client import PinotClient

CURSOR_VERSIONES = Cursor(CampoCursor("fecha_publicacion"), CampoCursor("idversion"))
ORDEN_VERSIONES = DESC  # la version reciente primero

CURSOR_ALCANCE = Cursor(CampoCursor("id_preferencia"))
ORDEN_ALCANCE = DESC

#: **Lista blanca.**
COLUMNAS_VERSION = (
    "idversion",
    "id_servicio",
    "version",
    "estado",
    "spec_url",
    "activo",
    "fecha_publicacion",
    "fecha_retiro",
)

#: **Lista blanca.** `telefono_sms` **no esta**: es dato personal de contacto y
#: el alcance de datos contratado se describe sin el.
COLUMNAS_ALCANCE = (
    "id_preferencia",
    "id_cliente",
    "frecuencia_reportes",
    "formato_reportes",
    "canales_notificacion",
    "zonas_geograficas",
    "destinatarios_reportes",
    "activo",
)


class InformesContratoRepository:
    """Solo lectura. Ningun metodo escribe ni publica en Kafka."""

    def __init__(self, pinot: PinotClient | None = None):
        self.pinot = pinot or PinotClient()

    # ── L4 — Versiones del contrato ──────────────────────────────────────────

    def versiones(
        self,
        *,
        cursor: tuple[Any, ...] | None = None,
        limit: int = 50,
        orden: Orden = ORDEN_VERSIONES,
        estado: str | None = None,
        id_servicio: int | None = None,
    ) -> list[dict[str, Any]]:
        """**Sin filtro de estado por defecto**: las retiradas tambien salen."""
        condiciones: list[str] = []
        params: dict[str, Any] = {"limit": limit + 1}

        if estado is not None:
            condiciones.append("estado = %(estado)s")
            params["estado"] = estado
        if id_servicio is not None:
            condiciones.append("id_servicio = %(id_servicio)s")
            params["id_servicio"] = id_servicio
        if cursor:
            condiciones.append(CURSOR_VERSIONES.clausula(orden))
            params.update(CURSOR_VERSIONES.params(cursor))

        sql = (
            f"SELECT {', '.join(COLUMNAS_VERSION)} FROM Dim_VersionContratoAPI"
            f"{_where(condiciones)} "
            f"ORDER BY {CURSOR_VERSIONES.order_by(orden)} LIMIT %(limit)s"
        )
        return self.pinot.query(sql, params)

    # ── L5 — Alcance de datos por cliente ────────────────────────────────────

    def alcance(
        self,
        *,
        cursor: tuple[Any, ...] | None = None,
        limit: int = 50,
        orden: Orden = ORDEN_ALCANCE,
        id_cliente: int | None = None,
        frecuencia: str | None = None,
    ) -> list[dict[str, Any]]:
        condiciones: list[str] = []
        params: dict[str, Any] = {"limit": limit + 1}

        if id_cliente is not None:
            condiciones.append("id_cliente = %(id_cliente)s")
            params["id_cliente"] = id_cliente
        if frecuencia is not None:
            condiciones.append("frecuencia_reportes = %(frecuencia)s")
            params["frecuencia"] = frecuencia
        if cursor:
            condiciones.append(CURSOR_ALCANCE.clausula(orden))
            params.update(CURSOR_ALCANCE.params(cursor))

        sql = (
            f"SELECT {', '.join(COLUMNAS_ALCANCE)} FROM Dim_Preferencias_Cliente"
            f"{_where(condiciones)} "
            f"ORDER BY {CURSOR_ALCANCE.order_by(orden)} LIMIT %(limit)s"
        )
        return self.pinot.query(sql, params)

    # ── Catalogos ────────────────────────────────────────────────────────────

    def nombres_de_servicio(self, idservicios: Sequence[int]) -> dict[int, str]:
        ids = sorted({i for i in idservicios if i is not None})
        if not ids:
            return {}

        filas = self.pinot.query(
            "SELECT id_servicio, nombre FROM Dim_Servicio "
            "WHERE id_servicio IN %(ids)s LIMIT %(limit)s",
            {"ids": ids, "limit": len(ids)},
        )
        return {f["id_servicio"]: f.get("nombre") for f in filas}

    def razones_sociales(self, idclientes: Sequence[int]) -> dict[int, str]:
        ids = sorted({i for i in idclientes if i is not None})
        if not ids:
            return {}

        filas = self.pinot.query(
            "SELECT idcliente, razon_social FROM Dim_Cliente "
            "WHERE idcliente IN %(ids)s LIMIT %(limit)s",
            {"ids": ids, "limit": len(ids)},
        )
        return {f["idcliente"]: f.get("razon_social") for f in filas}


def _where(condiciones: Sequence[str]) -> str:
    return f" WHERE {' AND '.join(condiciones)}" if condiciones else ""
