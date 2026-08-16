"""Consultas de los dos listados de OT17 — ciclo de vida de la cuenta.

L3 cuentas por estado · L4 transferencias de propiedad.

Aqui vive **el unico de los ocho listados que acepta rango de fechas**: L4 es de
*hechos del periodo* —una transferencia ocurre en un instante— mientras que los
otros siete describen el estado actual. Omitir el rango en L4 devuelve el
historico completo paginado, y **no es un error** (FR-013).

L3 incluye las cuentas dadas de baja
------------------------------------
La baja es logica: la fila sobrevive con su historial. Excluirlas convertiria el
listado de *ciclo de vida* en un listado de cuentas vivas, que es justo lo que no
se pide — el escenario 2 de la User Story 3 existe para impedirlo.
"""

from __future__ import annotations

from typing import Any, Sequence

from core.informes.paginacion import ASC, DESC, CampoCursor, Cursor, Orden
from core.pinot.client import PinotClient

CURSOR_CUENTAS = Cursor(CampoCursor("idcliente"))
ORDEN_CUENTAS = DESC  # lo mas reciente primero: `idcliente` crece con el alta

CURSOR_TRANSFERENCIAS = Cursor(
    CampoCursor("fechahora"), CampoCursor("idhistorialtransferencia")
)
ORDEN_TRANSFERENCIAS = DESC  # bitacora: el ultimo cambio de dueno es el relevante


class InformesCuentaRepository:
    """Solo lectura. Ningun metodo escribe ni publica en Kafka."""

    def __init__(self, pinot: PinotClient | None = None):
        self.pinot = pinot or PinotClient()

    # ── L3 — Cuentas por estado ──────────────────────────────────────────────

    def cuentas(
        self,
        *,
        cursor: tuple[Any, ...] | None = None,
        limit: int = 50,
        orden: Orden = ORDEN_CUENTAS,
        estado: str | None = None,
        tipo: str | None = None,
    ) -> list[dict[str, Any]]:
        """Cuentas con su estado. **Sin filtro de estado por defecto.**

        No excluir las dadas de baja es una decision, no un descuido: la baja es
        logica y la fila conserva su historial. Un listado de ciclo de vida que
        escondiera el final del ciclo no serviria para lo que se pide.
        """
        condiciones: list[str] = []
        params: dict[str, Any] = {"limit": limit + 1}

        if estado is not None:
            condiciones.append("estado = %(estado)s")
            params["estado"] = estado
        if tipo is not None:
            condiciones.append("tipo = %(tipo)s")
            params["tipo"] = tipo
        if cursor:
            condiciones.append(CURSOR_CUENTAS.clausula(orden))
            params.update(CURSOR_CUENTAS.params(cursor))

        sql = (
            "SELECT idcliente, razon_social, tipo, estado, estado_onboarding, "
            "fecha_inicio_contrato, admin_local_id FROM Dim_Cliente"
            f"{_where(condiciones)} "
            f"ORDER BY {CURSOR_CUENTAS.order_by(orden)} LIMIT %(limit)s"
        )
        return self.pinot.query(sql, params)

    # ── L4 — Transferencias de propiedad ─────────────────────────────────────

    def transferencias(
        self,
        *,
        cursor: tuple[Any, ...] | None = None,
        limit: int = 50,
        orden: Orden = ORDEN_TRANSFERENCIAS,
        desde_ms: int | None = None,
        hasta_ms: int | None = None,
        idcliente: int | None = None,
    ) -> list[dict[str, Any]]:
        """Bitacora de cambios de propietario, con **rango opcional** (FR-013).

        Los dos extremos son independientes: se puede pedir solo `desde`, solo
        `hasta`, ambos o ninguno. Ninguno devuelve el historico completo
        paginado, que es una respuesta valida y no una peticion incompleta.
        """
        condiciones: list[str] = []
        params: dict[str, Any] = {"limit": limit + 1}

        if desde_ms is not None:
            condiciones.append("fechahora >= %(desde_ms)s")
            params["desde_ms"] = desde_ms
        if hasta_ms is not None:
            # Inclusivo: `hasta_ms` ya es el ultimo milisegundo del dia pedido.
            condiciones.append("fechahora <= %(hasta_ms)s")
            params["hasta_ms"] = hasta_ms
        if idcliente is not None:
            condiciones.append("idcliente = %(idcliente)s")
            params["idcliente"] = idcliente
        if cursor:
            condiciones.append(CURSOR_TRANSFERENCIAS.clausula(orden))
            params.update(CURSOR_TRANSFERENCIAS.params(cursor))

        sql = (
            "SELECT idhistorialtransferencia, idcliente, idusuarioanterior, "
            "idusuarionuevo, fechahora FROM Fact_HistorialTransferenciaPropiedad"
            f"{_where(condiciones)} "
            f"ORDER BY {CURSOR_TRANSFERENCIAS.order_by(orden)} LIMIT %(limit)s"
        )
        return self.pinot.query(sql, params)

    # ── Catalogos ────────────────────────────────────────────────────────────

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
