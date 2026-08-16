"""Consulta de escalados — L2 de OT20.

⛔ El texto del mensaje no se consulta
--------------------------------------
`Fact_Historial_Ticket` guarda `mensaje` y `es_nota_interna`. **Ninguna de las
dos columnas aparece en la lista blanca**, y esa es toda la proteccion: no se
leen y luego se descartan, no se leen.

La alternativa —leerlas y filtrar despues— es como se resuelve hoy en la
pantalla operativa, y ahi tiene sentido porque la pantalla necesita el texto. Un
listado tactico no: responde **que paso, cuando y quien lo hizo**. Y un filtro
correcto sigue siendo un filtro que alguien puede olvidar al anadir un campo
dentro de seis meses, con un fallo silencioso —la respuesta conservaria la forma
esperada, solo que con notas internas dentro— (research D4).

⚠️ De once tipos de accion, exactamente dos son escalados
----------------------------------------------------------
Se incluyen `escalado_manual` y `escalado_automatico_sla`. Se excluyen, entre
otros:

* **`alerta_sla_riesgo`** — es un **aviso** de que el plazo se acerca; el ticket
  no cambia de agente ni de nivel. Contarlo inflaria el recuento de escalados
  con acciones que no derivaron nada;
* **`cierre_automatico_por_vencimiento`** — tambien es accion del sistema, pero
  **cierra** el ticket, no lo deriva.

El filtro es una **lista de inclusion**, no una exclusion: un tipo de accion
nuevo no entra solo en el listado de escalados (research D2).
"""

from __future__ import annotations

from typing import Any, Sequence

from core.informes.paginacion import DESC, CampoCursor, Cursor, Orden
from core.pinot.client import PinotClient

CURSOR_ESCALADOS = Cursor(CampoCursor("fecha_accion"), CampoCursor("id_historial"))
ORDEN_ESCALADOS = DESC

#: Los dos unicos tipos de accion que son un escalado (research D2).
ESCALADO_MANUAL = "escalado_manual"
ESCALADO_AUTOMATICO = "escalado_automatico_sla"
TIPOS_ESCALADO = (ESCALADO_MANUAL, ESCALADO_AUTOMATICO)

#: Nombres publicos del filtro `tipo_escalado`, y su tipo de accion interno.
TIPO_PUBLICO = {"manual": ESCALADO_MANUAL, "automatico": ESCALADO_AUTOMATICO}
TIPO_PUBLICO_INVERSO = {v: k for k, v in TIPO_PUBLICO.items()}

#: **Lista blanca.** Sin `mensaje` ni `es_nota_interna` (research D4).
COLUMNAS_ESCALADO = (
    "id_historial",
    "id_reclamo",
    "tipo_accion",
    "idusuario",
    "estado_anterior",
    "estado_nuevo",
    "fecha_accion",
)


class InformesEscaladosRepository:
    """Solo lectura. Ningun metodo escribe ni publica en Kafka."""

    def __init__(self, pinot: PinotClient | None = None):
        self.pinot = pinot or PinotClient()

    def escalados(
        self,
        *,
        cursor: tuple[Any, ...] | None = None,
        limit: int = 50,
        orden: Orden = ORDEN_ESCALADOS,
        tipo_escalado: str | None = None,
        id_reclamos: Sequence[int] | None = None,
        desde_ms: int | None = None,
        hasta_ms: int | None = None,
    ) -> list[dict[str, Any]]:
        """Escalados del periodo, con rango **opcional**.

        `id_reclamos` acota a los tickets de una cuenta: esta tabla guarda el
        ticket, no el cliente, asi que el filtro por cuenta se resuelve antes en
        **una** consulta, no una por fila.
        """
        condiciones: list[str] = []
        params: dict[str, Any] = {"limit": limit + 1}

        if tipo_escalado is not None:
            condiciones.append("tipo_accion = %(tipo_accion)s")
            params["tipo_accion"] = TIPO_PUBLICO[tipo_escalado]
        else:
            # Lista de inclusion, siempre presente: sin ella el listado seria
            # el historial entero, avisos y cierres incluidos.
            condiciones.append("tipo_accion IN %(tipos)s")
            params["tipos"] = list(TIPOS_ESCALADO)

        if id_reclamos is not None:
            if not id_reclamos:
                return []  # cuenta sin tickets: ningun escalado, sin ir a Pinot
            condiciones.append("id_reclamo IN %(id_reclamos)s")
            params["id_reclamos"] = list(id_reclamos)
        if desde_ms is not None:
            condiciones.append("fecha_accion >= %(desde_ms)s")
            params["desde_ms"] = desde_ms
        if hasta_ms is not None:
            condiciones.append("fecha_accion <= %(hasta_ms)s")
            params["hasta_ms"] = hasta_ms
        if cursor:
            condiciones.append(CURSOR_ESCALADOS.clausula(orden))
            params.update(CURSOR_ESCALADOS.params(cursor))

        sql = (
            f"SELECT {', '.join(COLUMNAS_ESCALADO)} FROM Fact_Historial_Ticket"
            f"{_where(condiciones)} "
            f"ORDER BY {CURSOR_ESCALADOS.order_by(orden)} LIMIT %(limit)s"
        )
        return self.pinot.query(sql, params)

    # ── Catalogos, resueltos por lote ────────────────────────────────────────

    def tickets_de_cuenta(self, idcliente: int) -> list[int]:
        """Tickets de una cuenta, para acotar el historial."""
        filas = self.pinot.query(
            "SELECT id_reclamo, idcliente FROM Fact_Reclamo "
            "WHERE idcliente = %(idcliente)s LIMIT 10000",
            {"idcliente": idcliente},
        )
        return sorted({f["id_reclamo"] for f in filas})

    def cuentas_de_ticket(self, id_reclamos: Sequence[int]) -> dict[int, int]:
        """`id_reclamo` → `idcliente`, para poner la cuenta en cada fila."""
        ids = _ids(id_reclamos)
        if not ids:
            return {}
        filas = self.pinot.query(
            "SELECT id_reclamo, idcliente FROM Fact_Reclamo "
            "WHERE id_reclamo IN %(ids)s LIMIT %(limit)s",
            {"ids": ids, "limit": len(ids)},
        )
        return {f["id_reclamo"]: f.get("idcliente") for f in filas}

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


def _ids(valores: Sequence[Any]) -> list[int]:
    return sorted({int(v) for v in valores if v is not None and int(v) > 0})


def _where(condiciones: Sequence[str]) -> str:
    return f" WHERE {' AND '.join(condiciones)}" if condiciones else ""
