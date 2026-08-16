"""Consulta de cambios de acceso — L3 de OT08/OT09.

**Aqui viven los motivos que el listado de credenciales no puede dar.**

`Dim_CredencialAPI` no sabe por que una credencial esta inactiva: revocacion,
cascada y expiracion son indistinguibles en ella (research D2). Esta bitacora si
lo sabe, porque **cada tipo de cambio es un valor propio**.

⚠️ Revocacion y cascada NO se agrupan
--------------------------------------
`revocacion_credencial` es una **decision de seguridad del partner**;
`desactivacion_por_cascada` es la consecuencia administrativa de una suspension
—tipicamente por impago—. Ponerlas en la misma linea induciria a reactivar una
credencial comprometida creyendo que solo habia una deuda pendiente, que es
exactamente lo que la regla de reactivacion selectiva previene.

⚠️ La reactivacion sin motivo es correcta (research D6)
--------------------------------------------------------
El SRS exige motivo **al cortar** el acceso, no al devolverlo. Una reactivacion
sin motivo no es un dato faltante: es la regla. Marcarla como incompleta
induciria a «corregir» algo que esta bien.
"""

from __future__ import annotations

from typing import Any, Sequence

from core.informes.paginacion import DESC, CampoCursor, Cursor, Orden
from core.pinot.client import PinotClient

CURSOR_BITACORA = Cursor(CampoCursor("fecha_cambio"), CampoCursor("idhistorial"))
ORDEN_BITACORA = DESC  # bitacora: el cambio reciente es el que importa

#: **Lista blanca.** Esta tabla no guarda secretos, pero la regla es la misma:
#: enumerar hace que una columna nueva no se publique sola.
COLUMNAS_BITACORA = (
    "idhistorial",
    "idpartner",
    "idcredencial",
    "tipo_cambio",
    "ejecutado_por",
    "motivo",
    "estado_anterior",
    "estado_nuevo",
    "fecha_cambio",
)


class InformesBitacoraRepository:
    """Solo lectura. Ningun metodo escribe ni publica en Kafka."""

    def __init__(self, pinot: PinotClient | None = None):
        self.pinot = pinot or PinotClient()

    def cambios(
        self,
        *,
        cursor: tuple[Any, ...] | None = None,
        limit: int = 50,
        orden: Orden = ORDEN_BITACORA,
        idpartners: Sequence[int] | None = None,
        idpartner: int | None = None,
        tipo_cambio: str | None = None,
        desde_ms: int | None = None,
        hasta_ms: int | None = None,
    ) -> list[dict[str, Any]]:
        """Cambios de acceso, con rango **opcional**.

        `idpartners` acota al conjunto de partners de una cuenta: la bitacora
        guarda el partner, no el cliente, asi que el acotamiento por cuenta se
        resuelve antes en **una** consulta.
        """
        condiciones: list[str] = []
        params: dict[str, Any] = {"limit": limit + 1}

        if idpartners is not None:
            if not idpartners:
                return []  # cuenta sin partners: ningun cambio, sin ir a Pinot
            condiciones.append("idpartner IN %(idpartners)s")
            params["idpartners"] = list(idpartners)
        if idpartner is not None:
            condiciones.append("idpartner = %(idpartner)s")
            params["idpartner"] = idpartner
        if tipo_cambio is not None:
            condiciones.append("tipo_cambio = %(tipo_cambio)s")
            params["tipo_cambio"] = tipo_cambio
        if desde_ms is not None:
            condiciones.append("fecha_cambio >= %(desde_ms)s")
            params["desde_ms"] = desde_ms
        if hasta_ms is not None:
            condiciones.append("fecha_cambio <= %(hasta_ms)s")
            params["hasta_ms"] = hasta_ms
        if cursor:
            condiciones.append(CURSOR_BITACORA.clausula(orden))
            params.update(CURSOR_BITACORA.params(cursor))

        sql = (
            f"SELECT {', '.join(COLUMNAS_BITACORA)} FROM Fact_HistorialAccesoPartner"
            f"{_where(condiciones)} "
            f"ORDER BY {CURSOR_BITACORA.order_by(orden)} LIMIT %(limit)s"
        )
        return self.pinot.query(sql, params)

    def partners_de_cuenta(self, idcliente: int) -> list[int]:
        """Partners de una cuenta, para acotar la bitacora."""
        filas = self.pinot.query(
            "SELECT idpartner, idcliente FROM Dim_Partner "
            "WHERE idcliente = %(idcliente)s LIMIT 1000",
            {"idcliente": idcliente},
        )
        return sorted({f["idpartner"] for f in filas})

    def nombres_de_partner(self, idpartners: Sequence[int]) -> dict[int, str]:
        ids = sorted({i for i in idpartners if i is not None})
        if not ids:
            return {}

        filas = self.pinot.query(
            "SELECT idpartner, nombrepartner FROM Dim_Partner "
            "WHERE idpartner IN %(ids)s LIMIT %(limit)s",
            {"ids": ids, "limit": len(ids)},
        )
        return {f["idpartner"]: f.get("nombrepartner") for f in filas}

    def nombres_de_credencial(self, idcredenciales: Sequence[int]) -> dict[int, str]:
        """Nombre de las credenciales citadas. **Sin tocar el secreto.**"""
        ids = sorted({i for i in idcredenciales if i is not None and int(i) > 0})
        if not ids:
            return {}

        filas = self.pinot.query(
            "SELECT idcredencial, nombre_credencial FROM Dim_CredencialAPI "
            "WHERE idcredencial IN %(ids)s LIMIT %(limit)s",
            {"ids": ids, "limit": len(ids)},
        )
        return {f["idcredencial"]: f.get("nombre_credencial") for f in filas}


def _where(condiciones: Sequence[str]) -> str:
    return f" WHERE {' AND '.join(condiciones)}" if condiciones else ""
