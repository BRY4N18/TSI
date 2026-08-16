"""Consultas de la nutricion del prospecto — L3 demos activas y L4 notificaciones.

⚠️ La expiracion de la demo no se puede comparar entera en SQL (research D3)
----------------------------------------------------------------------------
`demo_expiracion` esta declarada **`STRING`**, mientras que todas las demas
marcas de tiempo del sistema son `LONG` en milisegundos. Y el formato **no es
uniforme**: `apps/ventas_crm/demo_tokens.py` acepta defensivamente sufijo `Z`,
sufijo `+00:00` y cadenas **sin zona horaria**.

Comparar cadenas ISO-8601 lexicograficamente solo funciona si el formato es
identico en todas las filas. Con `Z` y `+00:00` conviviendo, la comparacion da
resultados incorrectos **sin ningun error visible**: unas demos vigentes
desaparecen del listado y nadie se entera.

**Filtro en dos pasos:**

1. **Aqui, en SQL**: prefiltro por el **prefijo de fecha** `YYYY-MM-DD` del dia
   actual. El prefijo `YYYY-MM-DD` **si** es uniforme sea cual sea el sufijo,
   asi que esa comparacion es segura.
2. **En el servicio**: refinamiento exacto con el instante actual, usando el
   parseador que ya tolera los tres formatos.

**Consecuencia declarada:** una pagina de este listado **puede devolver menos
filas que el `limit` pedido**, porque el servicio descarta las que expiraron hoy
mas temprano. `has_next` sigue siendo la autoridad; el numero de filas no lo es.

⚠️ `estado_envio` no se expone (L4)
-----------------------------------
La columna existe en el esquema y **ningun codigo la escribe**. Devolverla seria
presentar como dato algo que siempre esta vacio, y ademas invitaria a construir
encima un listado de "notificaciones con envio fallido" que no podria funcionar.
"""

from __future__ import annotations

from typing import Any, Sequence

from core.informes.paginacion import ASC, DESC, CampoCursor, Cursor, Orden
from core.pinot.client import PinotClient

#: El cursor de demos es **compuesto sobre texto**: `demo_expiracion` no es
#: unica ni numerica, asi que necesita el desempate por clave.
CURSOR_DEMOS = Cursor(
    CampoCursor("demo_expiracion", convertir=str), CampoCursor("idprospecto")
)
ORDEN_DEMOS = ASC  # las que vencen antes, primero: es lo que hay que atender ya

CURSOR_NOTIFICACIONES = Cursor(
    CampoCursor("fechahoranotificacion"), CampoCursor("idnotificacion")
)
ORDEN_NOTIFICACIONES = DESC  # lo mas reciente primero: la alerta fresca es la util


class InformesNutricionRepository:
    """Solo lectura. Ningun metodo escribe ni publica en Kafka."""

    def __init__(self, pinot: PinotClient | None = None):
        self.pinot = pinot or PinotClient()

    # ── L3 — Demos activas ───────────────────────────────────────────────────

    def demos_con_expiracion_desde(
        self,
        *,
        prefijo_hoy: str,
        cursor: tuple[Any, ...] | None = None,
        limit: int = 50,
        orden: Orden = ORDEN_DEMOS,
        titular: int | None = None,
    ) -> list[dict[str, Any]]:
        """Prefiltro por **prefijo de fecha**, nunca por la cadena completa.

        `prefijo_hoy` es `YYYY-MM-DD` del dia actual, calculado por el servicio
        con el mismo instante que usara para refinar. Que lo calcule el servicio
        y no este metodo es lo que permite inyectar el reloj y probarlo.

        La comparacion `>= 'YYYY-MM-DD'` es segura porque **cualquier** formato
        de los tres empieza por esos diez caracteres, y ordenan igual entre si.
        Trae de mas —las que expiraron hoy mas temprano— y eso es deliberado:
        el paso siguiente las descarta con precision de segundo.
        """
        condiciones = ["demo_expiracion >= %(prefijo_hoy)s"]
        params: dict[str, Any] = {"prefijo_hoy": prefijo_hoy, "limit": limit + 1}

        if titular is not None:
            condiciones.append("idusuario = %(titular)s")
            params["titular"] = titular
        if cursor:
            condiciones.append(CURSOR_DEMOS.clausula(orden))
            params.update(CURSOR_DEMOS.params(cursor))

        sql = (
            "SELECT idprospecto, empresa, nombres, apellidos, idusuario, demo_expiracion "
            "FROM Dim_Prospecto"
            f" WHERE {' AND '.join(condiciones)} "
            f"ORDER BY {CURSOR_DEMOS.order_by(orden)} LIMIT %(limit)s"
        )
        return self.pinot.query(sql, params)

    # ── L4 — Notificaciones enviadas ─────────────────────────────────────────

    def notificaciones(
        self,
        *,
        cursor: tuple[Any, ...] | None = None,
        limit: int = 50,
        orden: Orden = ORDEN_NOTIFICACIONES,
        titular: int | None = None,
        desde_ms: int | None = None,
        hasta_ms: int | None = None,
        regla: str | None = None,
        canal: str | None = None,
    ) -> list[dict[str, Any]]:
        """Alertas enviadas, acotadas por **destinatario**.

        El eje de titularidad aqui no es el ejecutivo asignado al prospecto sino
        `idusuariogerentenotificado`: el gerente ve aquellas de las que **fue
        destinatario**. Son cosas distintas y confundirlas mostraria alertas
        dirigidas a otro.

        `estado_envio` no aparece en las columnas enumeradas: nadie la escribe.
        """
        condiciones: list[str] = []
        params: dict[str, Any] = {"limit": limit + 1}

        if titular is not None:
            condiciones.append("idusuariogerentenotificado = %(titular)s")
            params["titular"] = titular
        if desde_ms is not None:
            condiciones.append("fechahoranotificacion >= %(desde_ms)s")
            params["desde_ms"] = desde_ms
        if hasta_ms is not None:
            condiciones.append("fechahoranotificacion <= %(hasta_ms)s")
            params["hasta_ms"] = hasta_ms
        if regla is not None:
            condiciones.append("regladisparada = %(regla)s")
            params["regla"] = regla
        if canal is not None:
            condiciones.append("canal = %(canal)s")
            params["canal"] = canal
        if cursor:
            condiciones.append(CURSOR_NOTIFICACIONES.clausula(orden))
            params.update(CURSOR_NOTIFICACIONES.params(cursor))

        sql = (
            "SELECT idnotificacion, id_prospecto, idusuariogerentenotificado, "
            "regladisparada, canal, fechahoranotificacion FROM Fact_NotificacionVentas"
            f"{_where(condiciones)} "
            f"ORDER BY {CURSOR_NOTIFICACIONES.order_by(orden)} LIMIT %(limit)s"
        )
        return self.pinot.query(sql, params)

    # ── Catalogos ────────────────────────────────────────────────────────────

    def empresas_de_prospecto(self, idprospectos: Sequence[int]) -> dict[int, str]:
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
