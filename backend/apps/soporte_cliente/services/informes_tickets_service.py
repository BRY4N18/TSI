"""Servicio de la cola de tickets — L1.

⚠️ Dos ausencias que significan cosas distintas
------------------------------------------------
Un ticket puede llegar sin `sla_status` de dos maneras, y confundirlas borra
justo lo que el listado existe para mostrar:

| Situacion | `sla_status` | Se presenta como |
|---|---|---|
| **Sin clasificar** | ausente | `situacion_compromiso: null` — aun no hay contador |
| **Sin compromiso** | `"sin compromiso"` | **su propio valor**, que es un dato, no una ausencia |

El segundo es un ticket **ya clasificado** al que no se le pudo asignar plazo. El
vigilante lo descarta precisamente por eso: es el unico estado en que un ticket
queda indefinidamente sin que ningun proceso lo mire. Colapsarlo a `null` —o
peor, a `en curso`— lo volveria invisible.
"""

from __future__ import annotations

from typing import Any

from core.informes.acotamiento import Acotamiento
from core.informes.formato import a_iso
from core.informes.paginacion import Orden, Pagina
from core.repositories.soporte.informes_tickets_repository import (
    CURSOR_TICKETS,
    ORDEN_TICKETS,
    InformesTicketsRepository,
)

#: Centinelas de «sin factura vinculada» en una columna STRING.
_SIN_FACTURA = ("", "null")


class InformesTicketsService:
    def __init__(self, repo: InformesTicketsRepository | None = None):
        self.repo = repo or InformesTicketsRepository()

    def tickets(
        self,
        *,
        acotamiento: Acotamiento,
        cursor: tuple[Any, ...] | None = None,
        limit: int = 50,
        orden: Orden = ORDEN_TICKETS,
        estado: str | None = None,
        situacion_compromiso: str | None = None,
        prioridad: str | None = None,
        tipo_incidencia: str | None = None,
        agente: int | None = None,
        con_factura: bool | None = None,
    ) -> Pagina:
        crudas = self.repo.tickets(
            cursor=cursor,
            limit=limit,
            orden=orden,
            idcliente=acotamiento.titular,
            estado=estado,
            situacion_compromiso=situacion_compromiso,
            prioridad=prioridad,
            tipo_incidencia=tipo_incidencia,
            agente=agente,
            con_factura=con_factura,
        )
        pagina = CURSOR_TICKETS.recortar(crudas, limit)

        cuentas = self.repo.razones_sociales(
            [f.get("idcliente") for f in pagina.filas]
        )
        agentes = self.repo.nombres_de_usuario(
            [f.get("id_agente_asignado") for f in pagina.filas]
        )
        servicios = self.repo.nombres_de_servicio(
            [f.get("idservicio") for f in pagina.filas]
        )

        return pagina._replace(
            filas=[
                {
                    # El numero de ticket es lenguaje de negocio, no una clave
                    # interna: es como el reportador nombra su incidencia.
                    "numero_ticket": fila.get("id_reclamo"),
                    "cuenta": cuentas.get(fila.get("idcliente")),
                    "asunto": fila.get("asunto"),
                    "estado": fila.get("estado"),
                    "prioridad": _vacio_a_none(fila.get("prioridad")),
                    "tipo_incidencia": _vacio_a_none(fila.get("tipo_incidencia")),
                    "servicio": servicios.get(_positivo(fila.get("idservicio"))),
                    # Ausente si nadie lo ha tomado. **La fila no se omite**:
                    # un ticket sin agente es el que mas necesita verse.
                    "agente_asignado": agentes.get(
                        _positivo(fila.get("id_agente_asignado"))
                    ),
                    # ⚠️ `sin compromiso` viaja tal cual. Solo el ticket **sin
                    # clasificar** llega con `null`, porque aun no hay contador.
                    "situacion_compromiso": _vacio_a_none(fila.get("sla_status")),
                    "factura_vinculada": _factura(fila.get("idfactura")),
                    "fecha_registro": a_iso(fila.get("fechahora")),
                }
                for fila in pagina.filas
            ]
        )


def _positivo(valor: Any) -> int | None:
    """Descarta los centinelas negativos con que Pinot marca un INT ausente."""
    if valor is None:
        return None
    try:
        entero = int(valor)
    except (TypeError, ValueError):
        return None
    return entero if entero > 0 else None


def _vacio_a_none(valor: Any) -> Any:
    """Un texto vacio es ausencia, no un valor configurado a nada."""
    if valor is None:
        return None
    texto = str(valor).strip()
    return None if texto in ("", "null") else texto


def _factura(valor: Any) -> str | None:
    """`''` y la cadena literal `'null'` significan «sin factura vinculada»."""
    if valor is None:
        return None
    texto = str(valor).strip()
    return None if texto in _SIN_FACTURA else texto
