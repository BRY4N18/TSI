"""Consulta de la cola de tickets — L1 de OT19.

⚠️ `sla_status` tiene CINCO valores, no cuatro
-----------------------------------------------
`data-model.md` enumera cuatro situaciones de compromiso. El dominio tiene
**cinco**: las cuatro declaradas mas `cumplido`, que `resolver_ticket_service`
escribe cuando un ticket se resuelve dentro de plazo.

Implementar las cuatro al pie de la letra dejaria el filtro rechazando con `400`
un valor legitimo —«no es valido» cuando si lo es— y haria **imposible listar
los tickets resueltos a tiempo**. Por eso los valores se **importan** de
`domain_constants`, no se copian de la spec.

⚠️ `sin compromiso` no es ausencia de dato
-------------------------------------------
Es un ticket **ya clasificado** al que no se le pudo asignar plazo. El vigilante
de plazos lo descarta precisamente por eso, asi que es el unico estado en que un
ticket puede quedarse indefinidamente sin que ningun proceso lo mire.

Omitirlo del listado, o presentarlo como `en curso`, reintroduciria el defecto
que la correccion anterior resolvio: volveria invisible justo lo que hay que ver.

Un ticket **sin clasificar** es otra cosa: llega sin `sla_status`, y no se le
atribuye ninguna situacion.

⛔ La descripcion del reporte no se consulta
--------------------------------------------
Lista blanca de columnas. `descripcion` es el cuerpo del ticket y no aporta a una
vista de cola (research D6); enumerar en vez de descartar hace ademas que una
columna nueva no se publique sola.
"""

from __future__ import annotations

from typing import Any, Sequence

from core.informes.paginacion import DESC, CampoCursor, Cursor, Orden
from core.pinot.client import PinotClient

CURSOR_TICKETS = Cursor(CampoCursor("fechahora"), CampoCursor("id_reclamo"))
ORDEN_TICKETS = DESC  # una cola de soporte se prioriza por plazo, no por antiguedad

#: **Lista blanca.** Sin `descripcion` (research D6).
COLUMNAS_TICKET = (
    "id_reclamo",
    "idcliente",
    "asunto",
    "estado",
    "prioridad",
    "tipo_incidencia",
    "idservicio",
    "id_agente_asignado",
    "sla_status",
    "idfactura",
    "fechahora",
)

#: Centinelas de «sin factura vinculada». `''` es el del dominio; `'null'` es el
#: que Pinot devuelve en una columna STRING sin valor, y hay que descartar los
#: dos: un `idfactura <> ''` a secas dejaria pasar la cadena literal `null` como
#: si fuera un numero de factura.
_SIN_FACTURA = ("", "null")


class InformesTicketsRepository:
    """Solo lectura. Ningun metodo escribe ni publica en Kafka."""

    def __init__(self, pinot: PinotClient | None = None):
        self.pinot = pinot or PinotClient()

    def tickets(
        self,
        *,
        cursor: tuple[Any, ...] | None = None,
        limit: int = 50,
        orden: Orden = ORDEN_TICKETS,
        idcliente: int | None = None,
        estado: str | None = None,
        situacion_compromiso: str | None = None,
        prioridad: str | None = None,
        tipo_incidencia: str | None = None,
        agente: int | None = None,
        con_factura: bool | None = None,
    ) -> list[dict[str, Any]]:
        """La cola, con los filtros combinables de FR-002."""
        condiciones: list[str] = []
        params: dict[str, Any] = {"limit": limit + 1}

        if idcliente is not None:
            condiciones.append("idcliente = %(idcliente)s")
            params["idcliente"] = idcliente
        if estado is not None:
            condiciones.append("estado = %(estado)s")
            params["estado"] = estado
        if situacion_compromiso is not None:
            # Se empuja tal cual: `sin compromiso` es un valor como los demas.
            condiciones.append("sla_status = %(sla_status)s")
            params["sla_status"] = situacion_compromiso
        if prioridad is not None:
            condiciones.append("prioridad = %(prioridad)s")
            params["prioridad"] = prioridad
        if tipo_incidencia is not None:
            condiciones.append("tipo_incidencia = %(tipo_incidencia)s")
            params["tipo_incidencia"] = tipo_incidencia
        if agente is not None:
            condiciones.append("id_agente_asignado = %(agente)s")
            params["agente"] = agente
        if con_factura is not None:
            operador = "NOT IN" if con_factura else "IN"
            condiciones.append(f"idfactura {operador} %(sin_factura)s")
            params["sin_factura"] = list(_SIN_FACTURA)
        if cursor:
            condiciones.append(CURSOR_TICKETS.clausula(orden))
            params.update(CURSOR_TICKETS.params(cursor))

        sql = (
            f"SELECT {', '.join(COLUMNAS_TICKET)} FROM Fact_Reclamo"
            f"{_where(condiciones)} "
            f"ORDER BY {CURSOR_TICKETS.order_by(orden)} LIMIT %(limit)s"
        )
        return self.pinot.query(sql, params)

    # ── Catalogos, resueltos por lote ────────────────────────────────────────

    def razones_sociales(self, idclientes: Sequence[int]) -> dict[int, str]:
        ids = _ids(idclientes)
        if not ids:
            return {}
        filas = self.pinot.query(
            "SELECT idcliente, razon_social FROM Dim_Cliente "
            "WHERE idcliente IN %(ids)s LIMIT %(limit)s",
            {"ids": ids, "limit": len(ids)},
        )
        return {f["idcliente"]: f.get("razon_social") for f in filas}

    def nombres_de_usuario(self, idusuarios: Sequence[int]) -> dict[int, str]:
        """Nombre del agente asignado. Sin correo ni ningun otro dato personal."""
        ids = _ids(idusuarios)
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
            or None
            for f in filas
        }

    def nombres_de_servicio(self, idservicios: Sequence[int]) -> dict[int, str]:
        ids = _ids(idservicios)
        if not ids:
            return {}
        filas = self.pinot.query(
            "SELECT id_servicio, nombre FROM Dim_Servicio "
            "WHERE id_servicio IN %(ids)s LIMIT %(limit)s",
            {"ids": ids, "limit": len(ids)},
        )
        return {f["id_servicio"]: f.get("nombre") for f in filas}


def _ids(valores: Sequence[Any]) -> list[int]:
    """Identificadores utiles, descartando ausencias y centinelas negativos."""
    return sorted(
        {int(v) for v in valores if v is not None and int(v) > 0}
    )


def _where(condiciones: Sequence[str]) -> str:
    return f" WHERE {' AND '.join(condiciones)}" if condiciones else ""
