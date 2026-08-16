"""Consultas de facturacion — L2 facturas y L4 metodos de pago vigentes.

⛔ El identificador de cobro no sale jamas (research D4)
-------------------------------------------------------
`Dim_MetodoPago.tokenpasarela` **no es un hash ni una referencia opaca
inofensiva**: `cobro_service.py:68` lo pasa a la pasarela para ejecutar el cargo.
**Quien lo tenga, puede cobrar.**

Por eso la consulta de metodos de pago **enumera sus columnas** y esta prohibido
`SELECT *`. El impacto de una fuga aqui no es informativo sino economico, y no
haria falta romper nada: bastaria con leer la respuesta.

⚠️ Una factura en disputa no es una factura impaga (research D3)
----------------------------------------------------------------
`estado_pago` toma **cuatro** valores, no tres. `En disputa` significa que el
cliente abrio un reclamo y el sistema **dejo de reintentar el cargo**.

El filtro de vencidas la excluye. Presentarla como mora induciria exactamente la
accion que la regla quiere evitar —perseguir un cobro que esta en discusion—,
que es lo que corrigio el hallazgo B41.

Nota sobre el nombre de la columna
-----------------------------------
`Fact_Factura` usa `id_cliente` **con guion bajo**, mientras que el resto de
tablas del departamento usan `idcliente`. Es una inconsistencia del esquema que
este repositorio absorbe para que ni el servicio ni la vista tengan que
conocerla.
"""

from __future__ import annotations

from typing import Any, Sequence

from core.informes.paginacion import ASC, DESC, CampoCursor, Cursor, Orden
from core.pinot.client import PinotClient

#: `id_factura` es `STRING`, no entero: el desempate compara texto. Es
#: determinista aunque no ordene numericamente, y eso basta — lo unico que el
#: cursor necesita garantizar es no repetir ni saltar filas.
CURSOR_FACTURAS = Cursor(
    CampoCursor("fecha_emision"), CampoCursor("id_factura", convertir=str)
)
ORDEN_FACTURAS = DESC  # la factura reciente es la que se esta cobrando

CURSOR_METODOS = Cursor(
    CampoCursor("fechaexpiracion"), CampoCursor("idmetodopago")
)
ORDEN_METODOS = ASC  # lo que antes caduca, primero: es lo que hay que renovar

#: Valores canonicos de `Fact_Factura.estado_pago`.
ESTADO_PENDIENTE = "Pendiente"
ESTADO_PAGADA = "Pagada"
ESTADO_FALLIDA = "Fallida"
#: Lo define el departamento de Partners y lo consume el de Suscripciones. Es
#: una rareza del modelo, no de esta spec: **no se duplica la constante**.
try:  # pragma: no cover - la importacion directa es la via normal
    from apps.partners.domain_constants import FACTURA_EN_DISPUTA as ESTADO_EN_DISPUTA
except Exception:  # pragma: no cover
    ESTADO_EN_DISPUTA = "En disputa"

ESTADOS_PAGO = (ESTADO_PENDIENTE, ESTADO_PAGADA, ESTADO_FALLIDA, ESTADO_EN_DISPUTA)

#: Los que **si** cuentan como mora cuando la factura ya vencio. `En disputa`
#: no esta, y `Pagada` tampoco.
ESTADOS_EN_MORA = (ESTADO_PENDIENTE, ESTADO_FALLIDA)


class InformesFacturacionRepository:
    """Solo lectura. Ningun metodo escribe ni publica en Kafka."""

    def __init__(self, pinot: PinotClient | None = None):
        self.pinot = pinot or PinotClient()

    # ── L2 — Facturas ────────────────────────────────────────────────────────

    def facturas(
        self,
        *,
        cursor: tuple[Any, ...] | None = None,
        limit: int = 50,
        orden: Orden = ORDEN_FACTURAS,
        cuenta: int | None = None,
        estado_pago: str | None = None,
        desde_ms: int | None = None,
        hasta_ms: int | None = None,
        vencidas_antes_de: int | None = None,
    ) -> list[dict[str, Any]]:
        """Facturas de la cuenta acotada, con rango **opcional**.

        `vencidas_antes_de` activa el filtro de mora: vencidas **y** en un estado
        que cuenta como impago. Las que estan en disputa quedan fuera aunque su
        fecha de vencimiento haya pasado.
        """
        condiciones: list[str] = []
        params: dict[str, Any] = {"limit": limit + 1}

        if cuenta is not None:
            # ⚠️ `id_cliente` con guion bajo: solo en esta tabla.
            condiciones.append("id_cliente = %(cuenta)s")
            params["cuenta"] = cuenta
        if estado_pago is not None:
            condiciones.append("estado_pago = %(estado_pago)s")
            params["estado_pago"] = estado_pago
        if desde_ms is not None:
            condiciones.append("fecha_emision >= %(desde_ms)s")
            params["desde_ms"] = desde_ms
        if hasta_ms is not None:
            condiciones.append("fecha_emision <= %(hasta_ms)s")
            params["hasta_ms"] = hasta_ms
        if vencidas_antes_de is not None:
            condiciones.append("fecha_vencimiento < %(vencidas_antes_de)s")
            params["vencidas_antes_de"] = vencidas_antes_de
            # La exclusion de la disputa vive **en la consulta**, no en Python:
            # filtrar despues de paginar devolveria paginas incompletas.
            condiciones.append("estado_pago IN %(estados_mora)s")
            params["estados_mora"] = list(ESTADOS_EN_MORA)
        if cursor:
            condiciones.append(CURSOR_FACTURAS.clausula(orden))
            params.update(CURSOR_FACTURAS.params(cursor))

        sql = (
            "SELECT id_factura, id_cliente, numero_factura, periodo, tipo, "
            "es_nota_credito, estado_pago, reintentos, monto_base, impuestos, "
            "monto_total, fecha_emision, fecha_vencimiento FROM Fact_Factura"
            f"{_where(condiciones)} "
            f"ORDER BY {CURSOR_FACTURAS.order_by(orden)} LIMIT %(limit)s"
        )
        return self.pinot.query(sql, params)

    # ── L4 — Metodos de pago vigentes ────────────────────────────────────────

    def metodos_de_pago(
        self,
        *,
        cursor: tuple[Any, ...] | None = None,
        limit: int = 50,
        orden: Orden = ORDEN_METODOS,
        cuenta: int | None = None,
        caduca_antes_de: int | None = None,
    ) -> list[dict[str, Any]]:
        """⛔ Columnas enumeradas: `tokenpasarela` no aparece y no puede salir.

        **Solo vigentes** (`activo = true`): reemplazar un metodo desactiva el
        anterior sin borrarlo, asi que este filtro es lo que distingue el medio
        de cobro real de su historial. Sin el, el listado mostraria tarjetas
        retiradas como si aun se pudieran cobrar.
        """
        condiciones = ["activo = true"]
        params: dict[str, Any] = {"limit": limit + 1}

        if cuenta is not None:
            condiciones.append("idcliente = %(cuenta)s")
            params["cuenta"] = cuenta
        if caduca_antes_de is not None:
            # La columna es `LONG`, asi que la comparacion va entera a la base
            # (research D5) — a diferencia del listado de demos de Ventas y CRM,
            # cuya columna equivalente era texto y obligo a un filtro en dos pasos.
            condiciones.append("fechaexpiracion <= %(caduca_antes_de)s")
            params["caduca_antes_de"] = caduca_antes_de
        if cursor:
            condiciones.append(CURSOR_METODOS.clausula(orden))
            params.update(CURSOR_METODOS.params(cursor))

        sql = (
            "SELECT idmetodopago, idcliente, tipo, ultimosdigitos, fechaexpiracion "
            "FROM Dim_MetodoPago"
            f" WHERE {' AND '.join(condiciones)} "
            f"ORDER BY {CURSOR_METODOS.order_by(orden)} LIMIT %(limit)s"
        )
        return self.pinot.query(sql, params)

    # ── Catalogo ─────────────────────────────────────────────────────────────

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
