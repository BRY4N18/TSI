"""Consulta de los cierres de caso — L5 de OT25.

⚠️ Una calificación ausente no es un cero
-------------------------------------------
En una escala, cero es el **peor valor posible**. Presentar «no se calificó»
como «se calificó con la nota mínima» invierte el significado en el punto donde
más engaña: un promedio que incluyera esos ceros hundiría la media sin que nadie
lo note, y la conclusión —«la atención es mala»— sería exactamente la contraria
de lo que dicen los datos.

`calificacion` es INT, así que su ausencia llega como el centinela negativo de
Pinot, no como `NULL`.

⚠️ Este listado es de ESTADO ACTUAL, no de período
----------------------------------------------------
`Fact_CierreAccidente` **no tiene fecha propia**: la hora de fin vive en el caso.
Filtrar cierres por fecha exigiría cruzar con `Fact_Accidente`, y eso lo haría
compuesto. Por eso rechaza el rango en vez de aceptarlo y aplicarlo a otra cosa.

Es la verificación que research D7 dejó pendiente, resuelta: **no hay columna
temporal en la tabla**, así que el listado se declara de estado actual.
"""

from __future__ import annotations

from typing import Any, Sequence

from core.informes.paginacion import DESC, CampoCursor, Cursor, Orden
from core.pinot.client import PinotClient

#: ⚠️ Escalar y de **texto**: el cierre es uno por caso, y el número de caso ya
#: desempata. Con el convertidor por defecto (`int`) la segunda página daría
#: `400`, y el listado sería inpaginable más allá de la primera.
CURSOR_CIERRES = Cursor(CampoCursor("idaccidente", str))
ORDEN_CIERRES = DESC

#: **Lista blanca.**
COLUMNAS_CIERRE = (
    "idaccidente",
    "resultado_atencion",
    "observaciones_finales",
    "calificacion",
)

#: Centinelas de ausencia en texto. Pinot no tiene NULL.
SIN_TEXTO = ("", "null")


class InformesCierresRepository:
    """Solo lectura. Ningun metodo escribe ni publica en Kafka."""

    def __init__(self, pinot: PinotClient | None = None):
        self.pinot = pinot or PinotClient()

    def cierres(
        self,
        *,
        cursor: tuple[Any, ...] | None = None,
        limit: int = 50,
        orden: Orden = ORDEN_CIERRES,
        resultado: str | None = None,
        sin_observaciones: bool | None = None,
        con_calificacion: bool | None = None,
    ) -> list[dict[str, Any]]:
        condiciones: list[str] = []
        params: dict[str, Any] = {"limit": limit + 1}

        if resultado is not None:
            condiciones.append("resultado_atencion = %(resultado)s")
            params["resultado"] = resultado
        if sin_observaciones is not None:
            params["sin_texto"] = list(SIN_TEXTO)
            operador = "IN" if sin_observaciones else "NOT IN"
            condiciones.append(f"observaciones_finales {operador} %(sin_texto)s")
        if con_calificacion is not None:
            # `> 0` y no `IS NOT NULL`: Pinot no tiene NULL, y el centinela de
            # un INT ausente es un negativo grande. Una guarda por nulidad
            # devolveria **todas** las filas como calificadas.
            operador = ">" if con_calificacion else "<="
            condiciones.append(f"calificacion {operador} 0")
        if cursor:
            condiciones.append(CURSOR_CIERRES.clausula(orden))
            params.update(CURSOR_CIERRES.params(cursor))

        sql = (
            f"SELECT {', '.join(COLUMNAS_CIERRE)} FROM Fact_CierreAccidente"
            f"{_where(condiciones)} "
            f"ORDER BY {CURSOR_CIERRES.order_by(orden)} LIMIT %(limit)s"
        )
        return self.pinot.query(sql, params)


def _where(condiciones: Sequence[str]) -> str:
    return f" WHERE {' AND '.join(condiciones)}" if condiciones else ""
