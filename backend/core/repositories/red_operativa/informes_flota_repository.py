"""Consulta de la composicion de la flota — L1 de OT12.

⚠️ Este listado informa de EXISTENCIA, no de DISPONIBILIDAD (research D2)
-------------------------------------------------------------------------
`Dim_UnidadEmergencia` **no tiene columna de estado operativo**. Los cuatro
estados —`Activa`, `Ocupada`, `En Mision`, `Fuera de servicio`— viven **solo en
el historico**, y obtenerlos cuesta **una consulta por unidad**.

Por eso este repositorio **no lee el historico de estados**, y es una decision,
no un olvido:

**`activo` significa «existe», no «puede acudir».** Un listado filtrado por
`activo = true` y presentado como flota disponible contaria unidades fuera de
servicio, ocupadas o ya en camino a otro accidente. En los modulos comerciales un
error asi infla una cifra; **aqui decide si alguien acude**.

La disponibilidad real es CU-T08, compuesta, y va sobre el modelo analitico.

⛔ Ni posicion ni contacto (research D6)
----------------------------------------
`latitud` y `longitud` son la **ultima posicion conocida** de la unidad, que la
constitucion trata como dato sensible sujeto a control de acceso y auditoria.
`contactoproveedor` es dato personal. Ninguno aporta a un listado de composicion
—para seguir una unidad en transito existe el modulo de seguimiento, con su
propio control—, asi que exponerlos ampliaria la superficie sin ganancia.

**Columnas enumeradas, prohibido `SELECT *`.**
"""

from __future__ import annotations

from typing import Any, Sequence

from core.informes.paginacion import DESC, CampoCursor, Cursor, Orden
from core.pinot.client import PinotClient

CURSOR_FLOTA = Cursor(CampoCursor("idunidademergencia"))
ORDEN_FLOTA = DESC

#: Lo que este listado describe. Viaja en `meta.alcance` para que ningun
#: consumidor lo lea como cobertura disponible (FR-008).
ALCANCE_COMPOSICION = "composicion_de_flota"


class InformesFlotaRepository:
    """Solo lectura. Ningun metodo escribe ni publica en Kafka."""

    def __init__(self, pinot: PinotClient | None = None):
        self.pinot = pinot or PinotClient()

    def unidades(
        self,
        *,
        cursor: tuple[Any, ...] | None = None,
        limit: int = 50,
        orden: Orden = ORDEN_FLOTA,
        proveedor: int | None = None,
        idcondado: int | None = None,
        tipo_unidad: str | None = None,
        dado_de_alta: bool | None = None,
    ) -> list[dict[str, Any]]:
        """Composicion de la flota, con columnas enumeradas.

        `dado_de_alta` filtra `activo`, que es **existencia**. No hay filtro de
        disponibilidad porque no hay dato de disponibilidad que filtrar.
        """
        condiciones: list[str] = []
        params: dict[str, Any] = {"limit": limit + 1}

        if proveedor is not None:
            condiciones.append("idcliente = %(proveedor)s")
            params["proveedor"] = proveedor
        if idcondado is not None:
            condiciones.append("idcondado = %(idcondado)s")
            params["idcondado"] = idcondado
        if tipo_unidad is not None:
            condiciones.append("tipounidademergencia = %(tipo_unidad)s")
            params["tipo_unidad"] = tipo_unidad
        if dado_de_alta is not None:
            condiciones.append("activo = %(dado_de_alta)s")
            params["dado_de_alta"] = dado_de_alta
        if cursor:
            condiciones.append(CURSOR_FLOTA.clausula(orden))
            params.update(CURSOR_FLOTA.params(cursor))

        sql = (
            "SELECT idunidademergencia, idcliente, placa, unidademergencia, "
            "tipounidademergencia, capacidad, idcondado, zonacobertura, "
            "tipopropiedad, activo FROM Dim_UnidadEmergencia"
            f"{_where(condiciones)} "
            f"ORDER BY {CURSOR_FLOTA.order_by(orden)} LIMIT %(limit)s"
        )
        return self.pinot.query(sql, params)

    def tipos_disponibles(self) -> list[str]:
        """Tipos de unidad presentes en los datos, para nombrar los validos."""
        filas = self.pinot.query(
            "SELECT idunidademergencia, tipounidademergencia FROM Dim_UnidadEmergencia "
            "LIMIT 10000"
        )
        return sorted({f["tipounidademergencia"] for f in filas if f.get("tipounidademergencia")})

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
