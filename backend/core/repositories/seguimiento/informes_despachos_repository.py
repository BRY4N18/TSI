"""Consulta del listado de despachos — L2 de OT22/OT23.

⚠️ «En tránsito» se deriva de las horas del propio despacho
------------------------------------------------------------
Despachado, **sin llegada y sin retiro**. No se consulta el histórico de estados
del despacho, por el mismo motivo que el listado de casos no consulta el suyo:
las horas son hechos del despacho, el estado formal no.

Aquí, además, la lectura es unívoca —una unidad despachada que no ha llegado ni
se ha retirado está en camino—, así que no hay nada que inferir.

⚠️ Las horas son LONG con `0` como centinela
----------------------------------------------
`fechahorallegada` y `fechahoraretiro` valen `0` cuando no han ocurrido. Una
guarda por nulidad sería siempre cierta y **ningún despacho** saldría como en
tránsito.

El retiro forzado se distingue del normal porque el despacho lo registra
explícitamente: es la traza de que la central retiró a una unidad en vez de que
la unidad terminara su parte.
"""

from __future__ import annotations

from typing import Any, Sequence

from core.informes.paginacion import DESC, CampoCursor, Cursor, Orden
from core.pinot.client import PinotClient

CURSOR_DESPACHOS = Cursor(CampoCursor("fechahoradespacho"), CampoCursor("iddespacho"))
ORDEN_DESPACHOS = DESC

#: **Lista blanca.**
COLUMNAS_DESPACHO = (
    "iddespacho",
    "idaccidente",
    "idunidademergencia",
    "idorigendespacho",
    "retiro_forzado",
    "fechahoradespacho",
    "fechahorallegada",
    "fechahoraretiro",
)

#: `0` es «aún no ha ocurrido», no la época de 1970.
SIN_HORA = 0


class InformesDespachosRepository:
    """Solo lectura. Ningun metodo escribe ni publica en Kafka."""

    def __init__(self, pinot: PinotClient | None = None):
        self.pinot = pinot or PinotClient()

    def despachos(
        self,
        *,
        cursor: tuple[Any, ...] | None = None,
        limit: int = 50,
        orden: Orden = ORDEN_DESPACHOS,
        idorigendespacho: int | None = None,
        idunidademergencia: int | None = None,
        idaccidente: str | None = None,
        en_transito: bool | None = None,
        desde_ms: int | None = None,
        hasta_ms: int | None = None,
    ) -> list[dict[str, Any]]:
        """Despachos del período, con rango **opcional**.

        Varios despachos sobre un mismo caso conviven, cada uno con sus horas:
        un caso puede acumular intentos de varios orígenes, y ocultarlos daría a
        entender que la asignación se resolvió a la primera.
        """
        condiciones: list[str] = []
        params: dict[str, Any] = {"limit": limit + 1, "sin_hora": SIN_HORA}

        if idorigendespacho is not None:
            condiciones.append("idorigendespacho = %(idorigendespacho)s")
            params["idorigendespacho"] = idorigendespacho
        if idunidademergencia is not None:
            condiciones.append("idunidademergencia = %(idunidademergencia)s")
            params["idunidademergencia"] = idunidademergencia
        if idaccidente is not None:
            condiciones.append("idaccidente = %(idaccidente)s")
            params["idaccidente"] = idaccidente
        if en_transito is True:
            condiciones.extend(
                [
                    "fechahoradespacho > %(sin_hora)s",
                    "fechahorallegada = %(sin_hora)s",
                    "fechahoraretiro = %(sin_hora)s",
                ]
            )
        elif en_transito is False:
            # Ya llegó **o** ya se retiró: dejó de estar en camino.
            condiciones.append(
                "(fechahorallegada > %(sin_hora)s OR fechahoraretiro > %(sin_hora)s)"
            )
        if desde_ms is not None:
            condiciones.append("fechahoradespacho >= %(desde_ms)s")
            params["desde_ms"] = desde_ms
        if hasta_ms is not None:
            condiciones.append("fechahoradespacho <= %(hasta_ms)s")
            params["hasta_ms"] = hasta_ms
        if cursor:
            condiciones.append(CURSOR_DESPACHOS.clausula(orden))
            params.update(CURSOR_DESPACHOS.params(cursor))

        sql = (
            f"SELECT {', '.join(COLUMNAS_DESPACHO)} FROM Fact_Despacho"
            f"{_where(condiciones)} "
            f"ORDER BY {CURSOR_DESPACHOS.order_by(orden)} LIMIT %(limit)s"
        )
        return self.pinot.query(sql, params)

    # ── Catalogos, resueltos por lote ────────────────────────────────────────

    def unidades(self, idunidades: Sequence[int]) -> dict[int, str]:
        """Nombre de la unidad. ⛔ **Sin su posición ni el contacto del proveedor**.

        `Dim_UnidadEmergencia` guarda latitud, longitud y `contactoproveedor`.
        Ninguno entra: es la misma exclusión que Red Operativa ya aplica.
        """
        ids = _ids(idunidades)
        if not ids:
            return {}
        filas = self.pinot.query(
            "SELECT idunidademergencia, unidademergencia FROM Dim_UnidadEmergencia "
            "WHERE idunidademergencia IN %(ids)s LIMIT %(limit)s",
            {"ids": ids, "limit": len(ids)},
        )
        return {
            f["idunidademergencia"]: f.get("unidademergencia") for f in filas
        }

    def origenes(self, idorigenes: Sequence[int]) -> dict[int, str]:
        ids = _ids(idorigenes)
        if not ids:
            return {}
        filas = self.pinot.query(
            "SELECT idorigendespacho, origendespacho FROM Dim_OrigenDespacho "
            "WHERE idorigendespacho IN %(ids)s LIMIT %(limit)s",
            {"ids": ids, "limit": len(ids)},
        )
        return {f["idorigendespacho"]: f.get("origendespacho") for f in filas}


def _ids(valores: Sequence[Any]) -> list[int]:
    return sorted({int(v) for v in valores if v is not None and int(v) > 0})


def _where(condiciones: Sequence[str]) -> str:
    return f" WHERE {' AND '.join(condiciones)}" if condiciones else ""
