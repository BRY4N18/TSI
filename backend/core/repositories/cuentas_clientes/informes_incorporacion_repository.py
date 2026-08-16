"""Consultas de los dos listados de OT04 — incorporacion de clientes nuevos.

L1 solicitudes de alta pendientes · L2 incorporacion incompleta.

Los dos son **bandejas de trabajo**, no informes de gestion: quien los abre va a
actuar sobre lo que ve. De ahi que ambos ordenen **ascendente por fecha** —lo que
lleva mas tiempo detenido va primero—, al reves que un listado de consulta.

El filtro de antiguedad viaja a Pinot
--------------------------------------
`dias_minimo` no se aplica en Python sobre el resultado: se traduce a una
**fecha de corte** que entra en el `WHERE` (research D5). Filtrar despues de
paginar devolveria paginas incompletas —o vacias— sin que nada avisara, porque
el `LIMIT` ya habria recortado antes de descartar.
"""

from __future__ import annotations

from typing import Any, Sequence

from core.informes.paginacion import ASC, CampoCursor, Cursor, Orden
from core.pinot.client import PinotClient
from core.repositories.cuentas_clientes.cliente_repository import (
    ESTADO_CLIENTE_PENDIENTE,
)

CURSOR_SOLICITUDES = Cursor(CampoCursor("fecha_creacion"), CampoCursor("idcliente"))
ORDEN_SOLICITUDES = ASC  # bandeja: la solicitud mas antigua es la mas urgente

CURSOR_ONBOARDING = Cursor(
    CampoCursor("fecha_actualizacion"), CampoCursor("id_onboarding")
)
ORDEN_ONBOARDING = ASC  # bandeja: quien lleva mas tiempo detenido, primero


class InformesIncorporacionRepository:
    """Solo lectura. Ningun metodo escribe ni publica en Kafka."""

    def __init__(self, pinot: PinotClient | None = None):
        self.pinot = pinot or PinotClient()

    # ── L1 — Solicitudes de alta pendientes ──────────────────────────────────

    def solicitudes_pendientes(
        self,
        *,
        cursor: tuple[Any, ...] | None = None,
        limit: int = 50,
        orden: Orden = ORDEN_SOLICITUDES,
        tipo: str | None = None,
        creadas_antes_de: int | None = None,
    ) -> list[dict[str, Any]]:
        """Solicitudes esperando aprobacion.

        `creadas_antes_de` es la fecha de corte ya calculada por el servicio a
        partir de `dias_minimo`: el repositorio no consulta el reloj, para que el
        calculo sea verificable con un instante inyectado (research D5).
        """
        condiciones = ["estado = %(estado)s"]
        params: dict[str, Any] = {
            "estado": ESTADO_CLIENTE_PENDIENTE,
            "limit": limit + 1,
        }

        if tipo is not None:
            condiciones.append("tipo = %(tipo)s")
            params["tipo"] = tipo
        if creadas_antes_de is not None:
            condiciones.append("fecha_creacion <= %(creadas_antes_de)s")
            params["creadas_antes_de"] = creadas_antes_de
        if cursor:
            condiciones.append(CURSOR_SOLICITUDES.clausula(orden))
            params.update(CURSOR_SOLICITUDES.params(cursor))

        sql = (
            "SELECT idcliente, razon_social, tipo, fecha_creacion FROM Dim_Cliente"
            f" WHERE {' AND '.join(condiciones)} "
            f"ORDER BY {CURSOR_SOLICITUDES.order_by(orden)} LIMIT %(limit)s"
        )
        return self.pinot.query(sql, params)

    # ── L2 — Incorporacion incompleta ────────────────────────────────────────

    def etapas_pendientes(
        self,
        *,
        cursor: tuple[Any, ...] | None = None,
        limit: int = 50,
        orden: Orden = ORDEN_ONBOARDING,
        etapa: str | None = None,
        detenidas_antes_de: int | None = None,
    ) -> list[dict[str, Any]]:
        """Una fila por **etapa pendiente que ya tiene registro**.

        No se infieren las etapas que aun no existen (research D6). Inferirlas
        exigiria cruzar con un catalogo de etapas esperadas y calcular la
        diferencia — una operacion de conjunto que empujaria el listado hacia lo
        compuesto, y la pregunta real del Administrador («¿quien esta detenido y
        donde?») ya la responde una fila pendiente.
        """
        condiciones = ["completado = false"]
        params: dict[str, Any] = {"limit": limit + 1}

        if etapa is not None:
            condiciones.append("etapa = %(etapa)s")
            params["etapa"] = etapa
        if detenidas_antes_de is not None:
            condiciones.append("fecha_actualizacion <= %(detenidas_antes_de)s")
            params["detenidas_antes_de"] = detenidas_antes_de
        if cursor:
            condiciones.append(CURSOR_ONBOARDING.clausula(orden))
            params.update(CURSOR_ONBOARDING.params(cursor))

        sql = (
            "SELECT id_onboarding, id_cliente, etapa, fecha_actualizacion FROM Fact_Onboarding"
            f" WHERE {' AND '.join(condiciones)} "
            f"ORDER BY {CURSOR_ONBOARDING.order_by(orden)} LIMIT %(limit)s"
        )
        return self.pinot.query(sql, params)

    def etapas_disponibles(self) -> list[str]:
        """Etapas que existen en los datos, para que un filtro invalido las nombre.

        Se leen de la tabla y no de una lista fija en codigo: el catalogo de
        etapas de incorporacion no vive en ninguna dimension, asi que una lista
        escrita a mano aqui quedaria desfasada en cuanto se anadiera una etapa,
        y rechazaria con `400` un valor perfectamente valido.
        """
        filas = self.pinot.query(
            "SELECT id_onboarding, etapa FROM Fact_Onboarding LIMIT 10000"
        )
        return sorted({f["etapa"] for f in filas if f.get("etapa")})

    # ── Catalogo ─────────────────────────────────────────────────────────────

    def razones_sociales(self, idclientes: Sequence[int]) -> dict[int, str]:
        """Resuelve `id_cliente` → razon social (research D6, `data-model` §2 L2)."""
        ids = sorted({i for i in idclientes if i is not None})
        if not ids:
            return {}

        filas = self.pinot.query(
            "SELECT idcliente, razon_social FROM Dim_Cliente "
            "WHERE idcliente IN %(ids)s LIMIT %(limit)s",
            {"ids": ids, "limit": len(ids)},
        )
        return {f["idcliente"]: f.get("razon_social") for f in filas}
