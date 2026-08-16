"""Consulta de la evidencia levantada en campo — L3 y L4 de OT24.

⚠️ La hora que vale es la del sitio, y las dos tablas la acompañan de otra
------------------------------------------------------------------------------
Es la regla central del módulo de evidencia, y las dos tablas **no son
simétricas**:

| Registro | Hora de captura | Hora de registro |
|---|---|---|
| **Fotografía** | `fechahora` | `fecha_sincronizacion` — **columna propia** |
| **Nota de campo** | `fechahora` | `fecha_actualizacion` — **marca genérica de la fila** |

La nota **no tiene columna de sincronización propia**. Tomar la columna
equivocada devolvería la hora de última modificación como si fuera la de
captura, y **el error sería invisible** en los registros hechos en línea —donde
ambas coinciden— apareciendo solo en los capturados sin conexión, que son
justamente los que importan.

Por eso las dos consultas viven en el mismo módulo pero **enumeran columnas
distintas**: la asimetría queda a la vista en vez de esconderse tras un nombre
compartido.

> **Deuda anotada.** Que la nota carezca de columna propia de sincronización es
> una asimetría del modelo, no de este listado. Mientras siga así, cualquier
> consulta sobre sincronización de notas depende de una columna genérica que
> cualquier actualización futura pisaría.
"""

from __future__ import annotations

from typing import Any, Sequence

from core.informes.paginacion import DESC, CampoCursor, Cursor, Orden
from core.pinot.client import PinotClient

CURSOR_FOTOS = Cursor(CampoCursor("fechahora"), CampoCursor("idevidenciafoto"))
CURSOR_NOTAS = Cursor(CampoCursor("fechahora"), CampoCursor("idnotaaccidentes"))
ORDEN_EVIDENCIA = DESC

#: **Lista blanca.** `fecha_sincronizacion` es la hora de registro **propia**.
COLUMNAS_FOTO = (
    "idevidenciafoto",
    "idaccidente",
    "idusuario",
    "sincronizado",
    "urlevidenciafoto",
    "fechahora",
    "fecha_sincronizacion",
)

#: **Lista blanca.** ⚠️ Aquí la hora de registro sale de `fecha_actualizacion`,
#: la marca genérica: esta tabla no tiene columna de sincronización.
COLUMNAS_NOTA = (
    "idnotaaccidentes",
    "idaccidente",
    "idusuario",
    "sincronizado",
    "nota",
    "tipo",
    "fechahora",
    "fecha_actualizacion",
)


class InformesEvidenciaRepository:
    """Solo lectura. Ningun metodo escribe ni publica en Kafka."""

    def __init__(self, pinot: PinotClient | None = None):
        self.pinot = pinot or PinotClient()

    def fotos(
        self,
        *,
        cursor: tuple[Any, ...] | None = None,
        limit: int = 50,
        orden: Orden = ORDEN_EVIDENCIA,
        sincronizado: bool | None = None,
        idaccidente: str | None = None,
        idusuario: int | None = None,
        desde_ms: int | None = None,
        hasta_ms: int | None = None,
    ) -> list[dict[str, Any]]:
        condiciones, params = _comunes(
            sincronizado, idaccidente, idusuario, desde_ms, hasta_ms, limit
        )
        if cursor:
            condiciones.append(CURSOR_FOTOS.clausula(orden))
            params.update(CURSOR_FOTOS.params(cursor))

        sql = (
            f"SELECT {', '.join(COLUMNAS_FOTO)} FROM Dim_EvidenciaFoto"
            f"{_where(condiciones)} "
            f"ORDER BY {CURSOR_FOTOS.order_by(orden)} LIMIT %(limit)s"
        )
        return self.pinot.query(sql, params)

    def notas(
        self,
        *,
        cursor: tuple[Any, ...] | None = None,
        limit: int = 50,
        orden: Orden = ORDEN_EVIDENCIA,
        sincronizado: bool | None = None,
        tipo: str | None = None,
        idaccidente: str | None = None,
        idusuario: int | None = None,
        desde_ms: int | None = None,
        hasta_ms: int | None = None,
    ) -> list[dict[str, Any]]:
        condiciones, params = _comunes(
            sincronizado, idaccidente, idusuario, desde_ms, hasta_ms, limit
        )
        if tipo is not None:
            condiciones.append("tipo = %(tipo)s")
            params["tipo"] = tipo
        if cursor:
            condiciones.append(CURSOR_NOTAS.clausula(orden))
            params.update(CURSOR_NOTAS.params(cursor))

        sql = (
            f"SELECT {', '.join(COLUMNAS_NOTA)} FROM Dim_NotaAccidente"
            f"{_where(condiciones)} "
            f"ORDER BY {CURSOR_NOTAS.order_by(orden)} LIMIT %(limit)s"
        )
        return self.pinot.query(sql, params)

    def autores(self, idusuarios: Sequence[int]) -> dict[int, str]:
        """Nombre de quien levantó la evidencia.

        Es personal de campo, no una persona implicada en el accidente: la
        exclusión de FR-016 no lo alcanza, y sin él la evidencia de dos unidades
        atendiendo el mismo caso se mezclaría.
        """
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


def _comunes(sincronizado, idaccidente, idusuario, desde_ms, hasta_ms, limit):
    condiciones: list[str] = []
    params: dict[str, Any] = {"limit": limit + 1}

    if sincronizado is not None:
        condiciones.append("sincronizado = %(sincronizado)s")
        params["sincronizado"] = sincronizado
    if idaccidente is not None:
        condiciones.append("idaccidente = %(idaccidente)s")
        params["idaccidente"] = idaccidente
    if idusuario is not None:
        condiciones.append("idusuario = %(idusuario)s")
        params["idusuario"] = idusuario
    if desde_ms is not None:
        # ⚠️ Sobre la hora de **captura**, no la de registro: el período que
        # interesa es cuándo ocurrió el levantamiento en el sitio.
        condiciones.append("fechahora >= %(desde_ms)s")
        params["desde_ms"] = desde_ms
    if hasta_ms is not None:
        condiciones.append("fechahora <= %(hasta_ms)s")
        params["hasta_ms"] = hasta_ms
    return condiciones, params


def _ids(valores: Sequence[Any]) -> list[int]:
    return sorted({int(v) for v in valores if v is not None and int(v) > 0})


def _where(condiciones: Sequence[str]) -> str:
    return f" WHERE {' AND '.join(condiciones)}" if condiciones else ""
