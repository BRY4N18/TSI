"""Consulta de las reasignaciones de cartera — L2 de OT02 / CU-O19.

Es de **hechos del periodo**: una reasignacion ocurre en un instante, asi que
acotarla por rango tiene sentido. Omitir el rango devuelve el historico completo
paginado, y **no es un error**.

No se acota por titularidad
---------------------------
A diferencia de los otros tres listados del departamento, este **no** tiene eje
de titularidad. Es supervision pura: el reparto de cartera es una decision
*sobre* el gerente, no una herramienta *suya*. Dársela acotada le mostraria de
quien recibio o a quien perdio prospectos —informacion de jefatura— disfrazada
de listado propio, asi que el permiso lo restringe al rol amplio y aqui no hay
columna que filtrar.
"""

from __future__ import annotations

from typing import Any, Sequence

from core.informes.paginacion import DESC, CampoCursor, Cursor, Orden
from core.pinot.client import PinotClient

CURSOR_ASIGNACIONES = Cursor(
    CampoCursor("fechahoraasignacion"), CampoCursor("idasignacion")
)
ORDEN_ASIGNACIONES = DESC  # bitacora: el ultimo movimiento es el relevante


class InformesAsignacionRepository:
    """Solo lectura. Ningun metodo escribe ni publica en Kafka."""

    def __init__(self, pinot: PinotClient | None = None):
        self.pinot = pinot or PinotClient()

    def reasignaciones(
        self,
        *,
        cursor: tuple[Any, ...] | None = None,
        limit: int = 50,
        orden: Orden = ORDEN_ASIGNACIONES,
        desde_ms: int | None = None,
        hasta_ms: int | None = None,
        idprospecto: int | None = None,
        tipo_asignacion: str | None = None,
    ) -> list[dict[str, Any]]:
        """Movimientos de cartera, con rango **opcional** en ambos extremos.

        Los dos extremos son independientes: se puede pedir solo `desde`, solo
        `hasta`, ambos o ninguno.
        """
        condiciones: list[str] = []
        params: dict[str, Any] = {"limit": limit + 1}

        if desde_ms is not None:
            condiciones.append("fechahoraasignacion >= %(desde_ms)s")
            params["desde_ms"] = desde_ms
        if hasta_ms is not None:
            # Inclusivo: `hasta_ms` ya es el ultimo milisegundo del dia pedido.
            condiciones.append("fechahoraasignacion <= %(hasta_ms)s")
            params["hasta_ms"] = hasta_ms
        if idprospecto is not None:
            condiciones.append("idprospecto = %(idprospecto)s")
            params["idprospecto"] = idprospecto
        if tipo_asignacion is not None:
            condiciones.append("tipoasignacion = %(tipo_asignacion)s")
            params["tipo_asignacion"] = tipo_asignacion
        if cursor:
            condiciones.append(CURSOR_ASIGNACIONES.clausula(orden))
            params.update(CURSOR_ASIGNACIONES.params(cursor))

        sql = (
            "SELECT idasignacion, idprospecto, idusuariogerenteanterior, "
            "idusuariogerenteactual, tipoasignacion, motivo, fechahoraasignacion "
            "FROM Fact_Asignacion"
            f"{_where(condiciones)} "
            f"ORDER BY {CURSOR_ASIGNACIONES.order_by(orden)} LIMIT %(limit)s"
        )
        return self.pinot.query(sql, params)

    def tipos_disponibles(self) -> list[str]:
        """Tipos de asignacion presentes en los datos, para nombrar los validos.

        Se leen de la tabla y no de una lista fija: el catalogo de tipos no vive
        en ninguna dimension, asi que una lista escrita a mano quedaria
        desfasada y rechazaria con `400` un valor perfectamente valido.
        """
        filas = self.pinot.query(
            "SELECT idasignacion, tipoasignacion FROM Fact_Asignacion LIMIT 10000"
        )
        return sorted({f["tipoasignacion"] for f in filas if f.get("tipoasignacion")})

    def empresas_de_prospecto(self, idprospectos: Sequence[int]) -> dict[int, str]:
        """Resuelve `idprospecto` → empresa, para no mostrar el numero."""
        ids = sorted({i for i in idprospectos if i is not None})
        if not ids:
            return {}

        filas = self.pinot.query(
            "SELECT idprospecto, empresa FROM Dim_Prospecto "
            "WHERE idprospecto IN %(ids)s LIMIT %(limit)s",
            {"ids": ids, "limit": len(ids)},
        )
        return {f["idprospecto"]: f.get("empresa") for f in filas}

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
