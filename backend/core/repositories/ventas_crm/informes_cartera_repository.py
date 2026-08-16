"""Consulta de la cartera de prospectos — L1 de OT01/OT02.

⚠️ «Perdido» no es «inactivo» (research D1)
-------------------------------------------
Un prospecto se vuelve inactivo por **dos motivos opuestos**, y los dos dejan
`activo = false`:

| Origen | Estado | Significado |
|---|---|---|
| `pipeline_service.py` | `motivo_inactividad = 'perdido'` | Se perdio la oportunidad |
| `conversion_cliente_service.py` | `motivo_inactividad = 'convertido'` | **Se gano** — ya es cliente |

**Esta prohibido usar `activo = false` como equivalente de «perdido».** Un
listado asi incluiria los convertidos, es decir **presentaria los exitos
comerciales como fracasos**. No fallaria ni daria error: mostraria un numero
plausible y equivocado.

Por eso el filtro `estado` tiene **tres** valores, no dos.

⚠️ Sin datos de contacto (research D4)
--------------------------------------
`Dim_Prospecto` guarda `gmail` y `telefono`. El proposito tactico es
**supervisar la cartera**, no contactar: para contactar existe la pantalla
operativa, que ya tiene esos datos y su control de acceso. Columnas enumeradas,
prohibido `SELECT *` — de lo contrario un volcado del informe se convierte en
una lista de contactos exportable.

Exponer de menos es reversible; retirar un dato despues de que circule, no.
"""

from __future__ import annotations

from typing import Any, Sequence

from core.informes.paginacion import DESC, CampoCursor, Cursor, Orden
from core.pinot.client import PinotClient

CURSOR_CARTERA = Cursor(CampoCursor("idprospecto"))
ORDEN_CARTERA = DESC  # lo mas reciente primero: `idprospecto` crece con el alta

#: Motivos canonicos de `Dim_Prospecto.motivo_inactividad`, escritos por
#: `pipeline_service` y `conversion_cliente_service`.
MOTIVO_PERDIDO = "perdido"
MOTIVO_CONVERTIDO = "convertido"

ESTADO_ACTIVO = "activo"
ESTADO_PERDIDO = "perdido"
ESTADO_CONVERTIDO = "convertido"

#: Los tres valores del filtro, con la condicion que **de verdad** los
#: distingue. Vive como tabla y no como `if` encadenado para que la equivalencia
#: prohibida —`perdido` = `activo = false`— no pueda colarse sin verse.
CONDICION_POR_ESTADO: dict[str, tuple[str, dict[str, Any]]] = {
    ESTADO_ACTIVO: ("activo = true", {}),
    ESTADO_PERDIDO: (
        "motivo_inactividad = %(motivo)s",
        {"motivo": MOTIVO_PERDIDO},
    ),
    ESTADO_CONVERTIDO: (
        "motivo_inactividad = %(motivo)s",
        {"motivo": MOTIVO_CONVERTIDO},
    ),
}

ESTADOS_VALIDOS = tuple(CONDICION_POR_ESTADO)


class InformesCarteraRepository:
    """Solo lectura. Ningun metodo escribe ni publica en Kafka."""

    def __init__(self, pinot: PinotClient | None = None):
        self.pinot = pinot or PinotClient()

    def prospectos(
        self,
        *,
        cursor: tuple[Any, ...] | None = None,
        limit: int = 50,
        orden: Orden = ORDEN_CARTERA,
        titular: int | None = None,
        canal: str | None = None,
        tipo_organizacion: str | None = None,
        etapa: str | None = None,
        estado: str | None = None,
    ) -> list[dict[str, Any]]:
        """Cartera con columnas enumeradas — sin `gmail` ni `telefono`.

        `titular` lo decide el resolutor de acotamiento; aqui solo se sabe **por
        que columna** se aplica (`idusuario`, el ejecutivo asignado). Esa
        separacion es la que permite reutilizar el resolutor en los seis
        departamentos restantes, donde el eje sera cliente, partner o proveedor.
        """
        condiciones: list[str] = []
        params: dict[str, Any] = {"limit": limit + 1}

        if titular is not None:
            condiciones.append("idusuario = %(titular)s")
            params["titular"] = titular
        if canal is not None:
            condiciones.append("como_nos_conocio = %(canal)s")
            params["canal"] = canal
        if tipo_organizacion is not None:
            condiciones.append("tipo_organizacion = %(tipo_organizacion)s")
            params["tipo_organizacion"] = tipo_organizacion
        if etapa is not None:
            condiciones.append("etapa_actual = %(etapa)s")
            params["etapa"] = etapa
        if estado is not None:
            sql_estado, params_estado = CONDICION_POR_ESTADO[estado]
            condiciones.append(sql_estado)
            params.update(params_estado)
        if cursor:
            condiciones.append(CURSOR_CARTERA.clausula(orden))
            params.update(CURSOR_CARTERA.params(cursor))

        sql = (
            "SELECT idprospecto, empresa, nombres, apellidos, cargo, tipo_organizacion, "
            "como_nos_conocio, etapa_actual, idusuario, activo, motivo_inactividad, "
            "valor_estimado, fecha_registro FROM Dim_Prospecto"
            f"{_where(condiciones)} "
            f"ORDER BY {CURSOR_CARTERA.order_by(orden)} LIMIT %(limit)s"
        )
        return self.pinot.query(sql, params)

    def motivos_de_perdida(self, idprospectos: Sequence[int]) -> dict[int, str]:
        """`motivo_perdida` de los prospectos perdidos **de la pagina resuelta**.

        Vive en la transicion del embudo (`Fact_Pipeline`), no en el prospecto:
        `Dim_Prospecto.motivo_inactividad` solo guarda la **categoria**
        (`perdido` / `convertido`), no la razon.

        **Sobre la regla de «una sola tabla».** El contrato prohibe cruzar dos
        tablas de *hechos*; aqui se resuelve un atributo por fila contra una
        transicion concreta, sin `GROUP BY` ni metrica, y acotado a los
        prospectos de la pagina. Es la misma forma que la resolucion de catalogo
        que el contrato si permite. La alternativa era retirar del contrato un
        campo que declara, y dejar «perdido» sin explicar.

        Si hubiera varias transiciones a «Perdido» se toma **la mas reciente**,
        que es el estado vigente; sin ese desempate el resultado dependeria del
        orden de llegada.
        """
        if not idprospectos:
            return {}

        filas = self.pinot.query(
            "SELECT id_prospecto, motivo_perdida, fecha_transicion FROM Fact_Pipeline "
            "WHERE id_prospecto IN %(ids)s AND etapa_nueva = %(etapa)s "
            "ORDER BY fecha_transicion DESC LIMIT %(limit)s",
            {
                "ids": list(idprospectos),
                "etapa": "Perdido",
                "limit": len(idprospectos) * 10,
            },
        )

        motivos: dict[int, str] = {}
        for fila in filas:  # ya vienen de mas reciente a mas antigua
            pid = fila["id_prospecto"]
            if pid not in motivos and fila.get("motivo_perdida"):
                motivos[pid] = fila["motivo_perdida"]
        return motivos

    def nombres_de_usuario(self, idusuarios: Sequence[int]) -> dict[int, str]:
        """Resuelve `idusuario` → nombre del ejecutivo."""
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
