"""Consultas de regiones e intentos de validacion — L3 y L4 de OT11/OT13.

⚠️ Cinco estados, y dos no significan lo que parecen (research D4)
------------------------------------------------------------------
| Estado | Significa |
|---|---|
| `En_Validación` | Aun no opera |
| `Producción` | Opera con normalidad |
| **`En_Alerta`** | **Opera, con cobertura degradada** |
| `Despublicada` | Ya no opera |
| `Rechazada` | Descartada tras validacion fallida |

**`En_Alerta` no se agrupa con `Despublicada`.** Es una region **operativa** cuya
cobertura se degrado: es candidata a despublicarse, no despublicada. Agruparlas
ocultaria exactamente la ventana en la que OT13 puede actuar —retirar una region
*antes* de que se quede sin continuidad—. Es la misma clase de error que
confundir «en disputa» con «impaga» en Suscripciones.

⚠️ Se conservan TODOS los intentos de validacion (FR-005)
----------------------------------------------------------
Dos rechazos sobre la misma region son **dos entradas**, cada una con su motivo.
El segundo no sustituye al primero: el historial de por que se rechazo una region
es lo que permite al Director Tecnologico ajustar los criterios.
"""

from __future__ import annotations

from typing import Any, Sequence

from core.informes.paginacion import DESC, CampoCursor, Cursor, Orden
from core.pinot.client import PinotClient

CURSOR_REGIONES = Cursor(CampoCursor("idregionoperativa"))
ORDEN_REGIONES = DESC

CURSOR_VALIDACIONES = Cursor(
    CampoCursor("fechahora"), CampoCursor("idvalidacionregion")
)
ORDEN_VALIDACIONES = DESC

#: Los cinco. **Ninguno se agrupa con otro.**
ESTADO_EN_VALIDACION = "En_Validación"
ESTADO_PRODUCCION = "Producción"
ESTADO_EN_ALERTA = "En_Alerta"
ESTADO_DESPUBLICADA = "Despublicada"
ESTADO_RECHAZADA = "Rechazada"

ESTADOS_REGION = (
    ESTADO_EN_VALIDACION,
    ESTADO_PRODUCCION,
    ESTADO_EN_ALERTA,
    ESTADO_DESPUBLICADA,
    ESTADO_RECHAZADA,
)

#: Las que **siguen operando**. `En_Alerta` esta aqui a proposito: opera con
#: cobertura degradada, y es donde OT13 puede actuar antes de perderla.
ESTADOS_OPERATIVOS = (ESTADO_PRODUCCION, ESTADO_EN_ALERTA)


class InformesRegionRepository:
    """Solo lectura. Ningun metodo escribe ni publica en Kafka."""

    def __init__(self, pinot: PinotClient | None = None):
        self.pinot = pinot or PinotClient()

    # ── L3 — Regiones operativas ─────────────────────────────────────────────

    def regiones(
        self,
        *,
        cursor: tuple[Any, ...] | None = None,
        limit: int = 50,
        orden: Orden = ORDEN_REGIONES,
        estado_region: str | None = None,
        sin_cambio_desde: int | None = None,
    ) -> list[dict[str, Any]]:
        """Regiones con su estado. **Sin filtro por defecto**: salen los cinco.

        `sin_cambio_desde` llega ya calculado por el servicio a partir de
        `detenida_mas_de_dias`: el repositorio no consulta el reloj, para que el
        calculo sea verificable con un instante inyectado.
        """
        condiciones: list[str] = []
        params: dict[str, Any] = {"limit": limit + 1}

        if estado_region is not None:
            condiciones.append("estadoregion = %(estado_region)s")
            params["estado_region"] = estado_region
        if sin_cambio_desde is not None:
            condiciones.append("fecha_actualizacion <= %(sin_cambio_desde)s")
            params["sin_cambio_desde"] = sin_cambio_desde
        if cursor:
            condiciones.append(CURSOR_REGIONES.clausula(orden))
            params.update(CURSOR_REGIONES.params(cursor))

        sql = (
            "SELECT idregionoperativa, idestado, nombreregion, estadoregion, "
            "activo, fecha_actualizacion FROM Dim_RegionOperativa"
            f"{_where(condiciones)} "
            f"ORDER BY {CURSOR_REGIONES.order_by(orden)} LIMIT %(limit)s"
        )
        return self.pinot.query(sql, params)

    # ── L4 — Intentos de validacion ──────────────────────────────────────────

    def validaciones(
        self,
        *,
        cursor: tuple[Any, ...] | None = None,
        limit: int = 50,
        orden: Orden = ORDEN_VALIDACIONES,
        idregion: int | None = None,
        resultado: str | None = None,
        desde_ms: int | None = None,
        hasta_ms: int | None = None,
    ) -> list[dict[str, Any]]:
        """**Todos** los intentos, con rango opcional. Ninguno sustituye a otro."""
        condiciones: list[str] = []
        params: dict[str, Any] = {"limit": limit + 1}

        if idregion is not None:
            condiciones.append("idregionoperativa = %(idregion)s")
            params["idregion"] = idregion
        if resultado is not None:
            condiciones.append("resultado = %(resultado)s")
            params["resultado"] = resultado
        if desde_ms is not None:
            condiciones.append("fechahora >= %(desde_ms)s")
            params["desde_ms"] = desde_ms
        if hasta_ms is not None:
            condiciones.append("fechahora <= %(hasta_ms)s")
            params["hasta_ms"] = hasta_ms
        if cursor:
            condiciones.append(CURSOR_VALIDACIONES.clausula(orden))
            params.update(CURSOR_VALIDACIONES.params(cursor))

        sql = (
            "SELECT idvalidacionregion, idregionoperativa, idusuario, resultado, "
            "motivo, fechahora FROM Dim_ValidacionRegion"
            f"{_where(condiciones)} "
            f"ORDER BY {CURSOR_VALIDACIONES.order_by(orden)} LIMIT %(limit)s"
        )
        return self.pinot.query(sql, params)

    def resultados_disponibles(self) -> list[str]:
        filas = self.pinot.query(
            "SELECT idvalidacionregion, resultado FROM Dim_ValidacionRegion LIMIT 10000"
        )
        return sorted({f["resultado"] for f in filas if f.get("resultado")})

    # ── Catalogos ────────────────────────────────────────────────────────────

    def nombres_de_estado(self, idestados: Sequence[int]) -> dict[int, str]:
        ids = sorted({i for i in idestados if i is not None})
        if not ids:
            return {}

        filas = self.pinot.query(
            "SELECT idestado, estado FROM Dim_Estado "
            "WHERE idestado IN %(ids)s LIMIT %(limit)s",
            {"ids": ids, "limit": len(ids)},
        )
        return {f["idestado"]: f.get("estado") for f in filas}

    def nombres_de_region(self, idregiones: Sequence[int]) -> dict[int, str]:
        ids = sorted({i for i in idregiones if i is not None})
        if not ids:
            return {}

        filas = self.pinot.query(
            "SELECT idregionoperativa, nombreregion FROM Dim_RegionOperativa "
            "WHERE idregionoperativa IN %(ids)s LIMIT %(limit)s",
            {"ids": ids, "limit": len(ids)},
        )
        return {f["idregionoperativa"]: f.get("nombreregion") for f in filas}

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
