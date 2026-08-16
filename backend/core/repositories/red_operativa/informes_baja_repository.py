"""Consulta de bajas de unidad — L2 de OT12 / CU-O42.

⚠️ Dos tipos de baja con significado muy distinto (research D5)
---------------------------------------------------------------
`baja_unidad_service.py:16-17` define `Normal` y `Forzada_con_reasignación`, y
el segundo se fija **cuando la unidad tenia un despacho activo**, guardando el
identificador del caso afectado.

**No es una etiqueta descriptiva: es la traza de impacto.** Una baja forzada
significa que un accidente se quedo sin la unidad que lo atendia y hubo que
reasignar. Un listado que sumara ambos tipos convertiria un incidente operativo
en una estadistica de rotacion de flota.
"""

from __future__ import annotations

from typing import Any, Sequence

from core.informes.paginacion import DESC, CampoCursor, Cursor, Orden
from core.pinot.client import PinotClient

CURSOR_BAJAS = Cursor(CampoCursor("fechahora"), CampoCursor("idbajaunidad"))
ORDEN_BAJAS = DESC  # bitacora: la baja reciente es la que importa

#: Se declaran aqui y **se comprueba contra el operativo en una prueba**:
#: `core/` no importa de `apps/`, pero divergir seria un filtro que devuelve
#: vacio con `200`.
TIPO_BAJA_NORMAL = "Normal"
TIPO_BAJA_FORZADA = "Forzada_con_reasignación"

TIPOS_BAJA = (TIPO_BAJA_NORMAL, TIPO_BAJA_FORZADA)


class InformesBajaRepository:
    """Solo lectura. Ningun metodo escribe ni publica en Kafka."""

    def __init__(self, pinot: PinotClient | None = None):
        self.pinot = pinot or PinotClient()

    def bajas(
        self,
        *,
        cursor: tuple[Any, ...] | None = None,
        limit: int = 50,
        orden: Orden = ORDEN_BAJAS,
        desde_ms: int | None = None,
        hasta_ms: int | None = None,
        tipo_baja: str | None = None,
        idunidades: Sequence[int] | None = None,
    ) -> list[dict[str, Any]]:
        """Bajas con rango **opcional**.

        `idunidades` acota a las unidades de un proveedor, resueltas antes: la
        tabla de bajas no guarda el proveedor, solo la unidad.
        """
        condiciones: list[str] = []
        params: dict[str, Any] = {"limit": limit + 1}

        if idunidades is not None:
            if not idunidades:
                return []  # proveedor sin unidades: ninguna baja, sin ir a Pinot
            condiciones.append("idunidademergencia IN %(idunidades)s")
            params["idunidades"] = list(idunidades)
        if tipo_baja is not None:
            condiciones.append("tipobaja = %(tipo_baja)s")
            params["tipo_baja"] = tipo_baja
        if desde_ms is not None:
            condiciones.append("fechahora >= %(desde_ms)s")
            params["desde_ms"] = desde_ms
        if hasta_ms is not None:
            condiciones.append("fechahora <= %(hasta_ms)s")
            params["hasta_ms"] = hasta_ms
        if cursor:
            condiciones.append(CURSOR_BAJAS.clausula(orden))
            params.update(CURSOR_BAJAS.params(cursor))

        sql = (
            "SELECT idbajaunidad, idunidademergencia, idusuario, idaccidente, "
            "motivo, tipobaja, fechahora FROM Fact_BajaUnidad"
            f"{_where(condiciones)} "
            f"ORDER BY {CURSOR_BAJAS.order_by(orden)} LIMIT %(limit)s"
        )
        return self.pinot.query(sql, params)

    def unidades_de_proveedor(self, idcliente: int) -> list[int]:
        """Identificadores de las unidades de un proveedor.

        Se resuelve antes de consultar las bajas porque `Fact_BajaUnidad` no
        guarda el proveedor. Es **una** consulta acotada, no una por fila.
        """
        filas = self.pinot.query(
            "SELECT idunidademergencia, idcliente FROM Dim_UnidadEmergencia "
            "WHERE idcliente = %(idcliente)s LIMIT 10000",
            {"idcliente": idcliente},
        )
        return sorted({f["idunidademergencia"] for f in filas})

    def datos_de_unidad(self, idunidades: Sequence[int]) -> dict[int, dict[str, Any]]:
        """Placa y proveedor de las unidades de la pagina."""
        ids = sorted({i for i in idunidades if i is not None})
        if not ids:
            return {}

        filas = self.pinot.query(
            "SELECT idunidademergencia, placa, idcliente FROM Dim_UnidadEmergencia "
            "WHERE idunidademergencia IN %(ids)s LIMIT %(limit)s",
            {"ids": ids, "limit": len(ids)},
        )
        return {
            f["idunidademergencia"]: {
                "placa": f.get("placa"),
                "idcliente": f.get("idcliente"),
            }
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
