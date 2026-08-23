"""Consultas de partners y credenciales — L1 y L2 de OT08.

⛔ Lista BLANCA de columnas, no lista negra de secretos (research D3)
---------------------------------------------------------------------
`Dim_CredencialAPI.client_secret_hash` es el secreto con el que un partner se
autentica contra la API. El modulo ya lo protegia, pero **con una lista negra**:
`consulta_partner_service.py:36` lee la fila entera y descarta los campos
prohibidos.

**Una lista negra falla abierta.** Si manana se anade una columna con material
sensible a la tabla, no estara en el conjunto prohibido y **saldra en la
respuesta** — y nadie lo notara, porque la respuesta seguira teniendo la forma
esperada, solo que con un campo de mas.

**Una lista blanca falla cerrada**: una columna nueva no aparece hasta que
alguien decida incluirla.

Las dos conviven porque no se estorban: la blanca protege estos listados, y la
negra sigue protegiendo el resto del modulo, que **no se toca**.

⚠️ El listado de credenciales no dice POR QUE esta inactiva (research D2)
-------------------------------------------------------------------------
Las tres razones —revocacion del partner, desactivacion en cascada por
suspension, y expiracion— son **indistinguibles en `Dim_CredencialAPI`**. Lo
documenta el propio servicio de reactivacion, que por eso lee la bitacora en vez
de preguntarle a la credencial.

Afirmar un motivo desde aqui seria inventarlo. Los motivos viven en la bitacora
de cambios de acceso (L3), cada uno con su tipo propio.
"""

from __future__ import annotations

from typing import Any, Sequence

from core.informes.paginacion import ASC, DESC, CampoCursor, Cursor, Orden
from core.pinot.client import PinotClient

CURSOR_PARTNERS = Cursor(CampoCursor("idpartner"))
ORDEN_PARTNERS = DESC

CURSOR_CREDENCIALES = Cursor(
    CampoCursor("fecha_expiracion"), CampoCursor("idcredencial")
)
ORDEN_CREDENCIALES = ASC  # lo que antes caduca, primero: es lo que hay que renovar

#: **Lista blanca.** Lo que sale de `Dim_Partner`. `contacto_tecnico_gmail` entra
#: porque el contrato lo pide para poder avisar al responsable tecnico; no hay
#: secreto en esta tabla.
COLUMNAS_PARTNER = (
    "idpartner",
    "idcliente",
    "nombrepartner",
    "planapi",
    "contacto_tecnico_nombre",
    "contacto_tecnico_gmail",
    "fecha_suspension",
    "motivo_suspension",
    "activo",
    "limitellamadasmes",
    "limitellamadasminuto",
    "sandbox_activado",
    "sandbox_expiracion",
)

#: **Lista blanca.** Lo que sale de `Dim_CredencialAPI`. `client_secret_hash`
#: **no esta**, y no por omision: enumerar es lo que hace que una columna
#: sensible anadida manana no se publique sola.
COLUMNAS_CREDENCIAL = (
    "idcredencial",
    "idpartner",
    "idcliente",
    "entorno",
    "activo",
    "nombre_credencial",
    "fecha_creacion",
    "fecha_expiracion",
)


class InformesAccesoRepository:
    """Solo lectura. Ningun metodo escribe ni publica en Kafka."""

    def __init__(self, pinot: PinotClient | None = None):
        self.pinot = pinot or PinotClient()

    # ── L1 — Partners ────────────────────────────────────────────────────────

    def partners(
        self,
        *,
        cursor: tuple[Any, ...] | None = None,
        limit: int = 50,
        orden: Orden = ORDEN_PARTNERS,
        cuenta: int | None = None,
        idpartner: int | None = None,
        plan: str | None = None,
        activo: bool | None = None,
        con_plan: bool | None = None,
    ) -> list[dict[str, Any]]:
        """Partners, con la parte del estado que **si** se puede filtrar en la base.

        El estado de incorporacion tiene seis valores y **cuatro de ellos no se
        derivan de esta tabla**: dependen de las credenciales del partner y de su
        bitacora. `activo` y `con_plan` son la parte pushable —suspendido y
        registrado—; el resto lo refina el servicio sobre la pagina ya resuelta.
        """
        condiciones: list[str] = []
        params: dict[str, Any] = {"limit": limit + 1}

        if cuenta is not None:
            condiciones.append("idcliente = %(cuenta)s")
            params["cuenta"] = cuenta
        if idpartner is not None:
            condiciones.append("idpartner = %(idpartner)s")
            params["idpartner"] = idpartner
        if plan is not None:
            condiciones.append("planapi = %(plan)s")
            params["plan"] = plan
        if activo is not None:
            condiciones.append("activo = %(activo)s")
            params["activo"] = activo
        if con_plan is not None:
            # Guarda contra el CENTINELA, no contra nulidad: un partner sin plan
            # lleva **cadena vacia**. `IS NOT NULL` seria siempre cierto.
            comparador = "<>" if con_plan else "="
            condiciones.append(f"planapi {comparador} %(sin_plan)s")
            params["sin_plan"] = ""
        if cursor:
            condiciones.append(CURSOR_PARTNERS.clausula(orden))
            params.update(CURSOR_PARTNERS.params(cursor))

        sql = (
            f"SELECT {', '.join(COLUMNAS_PARTNER)} FROM Dim_Partner"
            f"{_where(condiciones)} "
            f"ORDER BY {CURSOR_PARTNERS.order_by(orden)} LIMIT %(limit)s"
        )
        return self.pinot.query(sql, params)

    # ── L2 — Credenciales ────────────────────────────────────────────────────

    def credenciales(
        self,
        *,
        cursor: tuple[Any, ...] | None = None,
        limit: int = 50,
        orden: Orden = ORDEN_CREDENCIALES,
        cuenta: int | None = None,
        idpartner: int | None = None,
        entorno: str | None = None,
        activa: bool | None = None,
        caduca_antes_de: int | None = None,
    ) -> list[dict[str, Any]]:
        """⛔ Lista blanca: `client_secret_hash` no esta entre las columnas.

        **Sin campo de motivo**, y es deliberado (research D2): el registro de la
        credencial no lo contiene, y afirmarlo seria inventarlo.
        """
        condiciones: list[str] = []
        params: dict[str, Any] = {"limit": limit + 1}

        if cuenta is not None:
            condiciones.append("idcliente = %(cuenta)s")
            params["cuenta"] = cuenta
        if idpartner is not None:
            condiciones.append("idpartner = %(idpartner)s")
            params["idpartner"] = idpartner
        if entorno is not None:
            condiciones.append("entorno = %(entorno)s")
            params["entorno"] = entorno
        if activa is not None:
            condiciones.append("activo = %(activa)s")
            params["activa"] = activa
        if caduca_antes_de is not None:
            # La columna es `LONG`: la comparacion va entera a la base, sin el
            # rodeo en dos pasos que necesito el listado de demos de Ventas.
            condiciones.append("fecha_expiracion <= %(caduca_antes_de)s")
            params["caduca_antes_de"] = caduca_antes_de
        if cursor:
            condiciones.append(CURSOR_CREDENCIALES.clausula(orden))
            params.update(CURSOR_CREDENCIALES.params(cursor))

        sql = (
            f"SELECT {', '.join(COLUMNAS_CREDENCIAL)} FROM Dim_CredencialAPI"
            f"{_where(condiciones)} "
            f"ORDER BY {CURSOR_CREDENCIALES.order_by(orden)} LIMIT %(limit)s"
        )
        return self.pinot.query(sql, params)

    # ── Resolucion por lotes para derivar el estado ──────────────────────────

    def credenciales_de(self, idpartners: Sequence[int]) -> dict[int, list[dict]]:
        """Credenciales de los partners **de la pagina**, en una sola consulta.

        Una por partner seria N+1, que es justo lo que `derivar_estado` hace en
        el flujo operativo —correcto alli, porque resuelve un partner— y lo que
        aqui hay que evitar.
        """
        ids = sorted({i for i in idpartners if i is not None})
        if not ids:
            return {}

        filas = self.pinot.query(
            "SELECT idpartner, entorno, activo FROM Dim_CredencialAPI "
            "WHERE idpartner IN %(ids)s LIMIT %(limit)s",
            {"ids": ids, "limit": len(ids) * 50},
        )
        agrupado: dict[int, list[dict]] = {}
        for fila in filas:
            agrupado.setdefault(fila["idpartner"], []).append(fila)
        return agrupado

    def eventos_de(
        self, idpartners: Sequence[int], tipos: Sequence[str]
    ) -> dict[int, list[dict]]:
        """Eventos relevantes de la bitacora, tambien por lotes."""
        ids = sorted({i for i in idpartners if i is not None})
        if not ids or not tipos:
            return {}

        filas = self.pinot.query(
            "SELECT idpartner, tipo_cambio, fecha_cambio FROM Fact_HistorialAccesoPartner "
            "WHERE idpartner IN %(ids)s AND tipo_cambio IN %(tipos)s LIMIT %(limit)s",
            {"ids": ids, "tipos": list(tipos), "limit": len(ids) * 200},
        )
        agrupado: dict[int, list[dict]] = {}
        for fila in filas:
            agrupado.setdefault(fila["idpartner"], []).append(fila)
        return agrupado

    # ── Catalogos ────────────────────────────────────────────────────────────

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


def _where(condiciones: Sequence[str]) -> str:
    return f" WHERE {' AND '.join(condiciones)}" if condiciones else ""
