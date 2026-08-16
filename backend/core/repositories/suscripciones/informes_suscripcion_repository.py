"""Consulta de suscripciones — L1 de OT05/OT07.

⚠️ «Sin cambio de plan programado» es un centinela, no una ausencia (research D2)
--------------------------------------------------------------------------------
`cambio_plan_service.py:96` declara `SIN_CAMBIO_PROGRAMADO = 0`. Es decir: **toda
suscripcion sin cambio programado tiene un `0` guardado**, no un vacio.

Por eso el filtro compara **`idplan_programado > 0`**. Escribirlo como una
comprobacion de nulidad seria **siempre cierto** —la base analitica no almacena
nulos y aqui ademas el codigo escribe un `0` explicito—, asi que el filtro
devolveria **todas** las suscripciones como si todas tuvieran una reduccion
pendiente. No fallaria: daria un numero plausible y equivocado.

Las cancelaciones se filtran por columna, no por periodo
--------------------------------------------------------
`cancelada_desde` / `cancelada_hasta` acotan `fechacancelacion`. **No** son el
periodo generico del contrato: esta tabla guarda el **estado actual** de cada
suscripcion, no un historico de sucesos, asi que un rango generico no tendria
sobre que aplicarse.
"""

from __future__ import annotations

from typing import Any, Sequence

from core.informes.paginacion import ASC, DESC, CampoCursor, Cursor, Orden
from core.pinot.client import PinotClient

CURSOR_SUSCRIPCIONES = Cursor(CampoCursor("id_suscripcion"))
ORDEN_SUSCRIPCIONES = DESC

#: El valor que el codigo operativo escribe cuando **no** hay cambio programado.
#:
#: Se declara aqui y no se importa de `apps.suscripciones.services.cambio_plan_service`
#: —donde vive el original— porque `core/` no debe depender de `apps/`: seria
#: invertir el orden de las capas por una constante.
#:
#: A cambio, `test_informes_suscripcion_cambio_programado.py` comprueba que los
#: dos valores **coinciden**. Si el operativo cambiara, la prueba falla en vez de
#: dejar el informe filtrando contra un centinela obsoleto — que es justo el modo
#: de fallo que este proyecto ya sufrio con "ACTIVA" contra "Activo".
SIN_CAMBIO_PROGRAMADO = 0

#: Estados canonicos de `Fact_Suscripcion.estado`.
ESTADOS_SUSCRIPCION = ("Activa", "Suspendida", "Cancelada", "Vencida")


class InformesSuscripcionRepository:
    """Solo lectura. Ningun metodo escribe ni publica en Kafka."""

    def __init__(self, pinot: PinotClient | None = None):
        self.pinot = pinot or PinotClient()

    def suscripciones(
        self,
        *,
        cursor: tuple[Any, ...] | None = None,
        limit: int = 50,
        orden: Orden = ORDEN_SUSCRIPCIONES,
        cuenta: int | None = None,
        estado: str | None = None,
        idplan: int | None = None,
        con_cambio_programado: bool | None = None,
        vence_antes_de: int | None = None,
        cancelada_desde: int | None = None,
        cancelada_hasta: int | None = None,
    ) -> list[dict[str, Any]]:
        """Suscripciones de la cuenta acotada, o de todas.

        `vence_antes_de` y los extremos de cancelacion llegan ya calculados por
        el servicio: el repositorio no consulta el reloj, para que el calculo
        sea verificable con un instante inyectado.
        """
        condiciones: list[str] = []
        params: dict[str, Any] = {"limit": limit + 1}

        if cuenta is not None:
            condiciones.append("idcliente = %(cuenta)s")
            params["cuenta"] = cuenta
        if estado is not None:
            condiciones.append("estado = %(estado)s")
            params["estado"] = estado
        if idplan is not None:
            condiciones.append("idplan = %(idplan)s")
            params["idplan"] = idplan
        if con_cambio_programado is not None:
            # ⚠️ Comparacion contra el centinela, **nunca** contra nulidad.
            comparador = ">" if con_cambio_programado else "<="
            condiciones.append(f"idplan_programado {comparador} %(sin_cambio)s")
            params["sin_cambio"] = SIN_CAMBIO_PROGRAMADO
        if vence_antes_de is not None:
            condiciones.append("fecha_fin <= %(vence_antes_de)s")
            params["vence_antes_de"] = vence_antes_de
        if cancelada_desde is not None:
            condiciones.append("fechacancelacion >= %(cancelada_desde)s")
            params["cancelada_desde"] = cancelada_desde
        if cancelada_hasta is not None:
            condiciones.append("fechacancelacion <= %(cancelada_hasta)s")
            params["cancelada_hasta"] = cancelada_hasta
        if cursor:
            condiciones.append(CURSOR_SUSCRIPCIONES.clausula(orden))
            params.update(CURSOR_SUSCRIPCIONES.params(cursor))

        sql = (
            "SELECT id_suscripcion, idcliente, idplan, idplan_programado, estado, "
            "nivel, precio, periodicidad, renovacionautomatica, motivocancelacion, "
            "fecha_inicio, fecha_fin, fechacancelacion FROM Fact_Suscripcion"
            f"{_where(condiciones)} "
            f"ORDER BY {CURSOR_SUSCRIPCIONES.order_by(orden)} LIMIT %(limit)s"
        )
        return self.pinot.query(sql, params)

    # ── Catalogos ────────────────────────────────────────────────────────────

    def nombres_de_plan(self, idplanes: Sequence[int]) -> dict[int, str]:
        """Resuelve `idplan` → nombre.

        Se descarta el centinela `0` antes de consultar: **no existe un plan con
        identificador cero** en el catalogo, asi que pedirlo seria una consulta
        garantizada a devolver nada.
        """
        ids = sorted({i for i in idplanes if i is not None and int(i) > 0})
        if not ids:
            return {}

        filas = self.pinot.query(
            "SELECT idplan, nombre FROM Dim_Plan WHERE idplan IN %(ids)s LIMIT %(limit)s",
            {"ids": ids, "limit": len(ids)},
        )
        return {f["idplan"]: f.get("nombre") for f in filas}

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
