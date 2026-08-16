"""Servicio de escalados — L2.

⚠️ La autoria se decide por la AUSENCIA de autor, no por el tipo de accion
--------------------------------------------------------------------------
La distincion entre un escalado que decidio una persona y uno que disparo el
sistema esta registrada **por duplicado**:

| Senal | Manual | Automatico |
|---|---|---|
| Tipo de accion | `escalado_manual` | `escalado_automatico_sla` |
| Autor | El agente que escalo | **Ausente** |

La ausencia de autor es deliberada y es la senal **autoritativa**: antes se
registraba al supervisor que **recibia** el escalado como si lo hubiera
ejecutado, y la correccion consistio en dejar el autor vacio y mover al
supervisor al campo de destinatario.

Por eso `tipo_escalado` se deriva del autor y no del tipo de accion. Si las dos
senales se contradijeran —un automatico con autor, o un manual sin el— el dato
estaria corrupto; decidir por el tipo de accion lo **ocultaria**, y apoyarse en
el autor lo hace visible. Hay una prueba que exige que coincidan en todos los
registros.

El resultado no atribuye el escalado automatico a nadie **ni lo deja en blanco a
secas**: el autor llega ausente y `tipo_escalado` dice `automatico`, que es el
campo donde vive esa informacion.
"""

from __future__ import annotations

from typing import Any

from core.informes.formato import a_iso
from core.informes.paginacion import Orden, Pagina
from core.repositories.soporte.informes_escalados_repository import (
    CURSOR_ESCALADOS,
    ORDEN_ESCALADOS,
    InformesEscaladosRepository,
)

TIPO_MANUAL = "manual"
TIPO_AUTOMATICO = "automatico"


class InformesEscaladosService:
    def __init__(self, repo: InformesEscaladosRepository | None = None):
        self.repo = repo or InformesEscaladosRepository()

    def escalados(
        self,
        *,
        cursor: tuple[Any, ...] | None = None,
        limit: int = 50,
        orden: Orden = ORDEN_ESCALADOS,
        tipo_escalado: str | None = None,
        cuenta: int | None = None,
        desde_ms: int | None = None,
        hasta_ms: int | None = None,
    ) -> Pagina:
        # El historial guarda el ticket, no el cliente: filtrar por cuenta
        # exige resolver sus tickets antes. **Una** consulta, no una por fila.
        id_reclamos = (
            self.repo.tickets_de_cuenta(cuenta) if cuenta is not None else None
        )

        crudas = self.repo.escalados(
            cursor=cursor,
            limit=limit,
            orden=orden,
            tipo_escalado=tipo_escalado,
            id_reclamos=id_reclamos,
            desde_ms=desde_ms,
            hasta_ms=hasta_ms,
        )
        pagina = CURSOR_ESCALADOS.recortar(crudas, limit)

        cuentas_por_ticket = self.repo.cuentas_de_ticket(
            [f.get("id_reclamo") for f in pagina.filas]
        )
        razones = self.repo.razones_sociales(list(cuentas_por_ticket.values()))
        autores = self.repo.nombres_de_usuario(
            [f.get("idusuario") for f in pagina.filas]
        )

        return pagina._replace(
            filas=[
                {
                    "numero_ticket": fila.get("id_reclamo"),
                    "cuenta": razones.get(
                        cuentas_por_ticket.get(fila.get("id_reclamo"))
                    ),
                    # ⚠️ Derivado del autor, no del tipo de accion (research D3).
                    "tipo_escalado": _tipo_por_autoria(fila),
                    "estado_anterior": _vacio_a_none(fila.get("estado_anterior")),
                    "estado_nuevo": _vacio_a_none(fila.get("estado_nuevo")),
                    # Ausente en los automaticos, y eso es la respuesta correcta:
                    # no hubo persona que lo decidiera.
                    "autor": autores.get(_autor(fila)),
                    "fecha": a_iso(fila.get("fecha_accion")),
                }
                for fila in pagina.filas
            ]
        )


def _autor(fila: dict[str, Any]) -> int | None:
    """El usuario que ejecuto la accion, o `None` si fue el sistema."""
    valor = fila.get("idusuario")
    if valor is None:
        return None
    try:
        entero = int(valor)
    except (TypeError, ValueError):
        return None
    return entero if entero > 0 else None


def _tipo_por_autoria(fila: dict[str, Any]) -> str:
    """Sin autor, accion del sistema. Es la senal autoritativa (research D3)."""
    return TIPO_MANUAL if _autor(fila) is not None else TIPO_AUTOMATICO


def _vacio_a_none(valor: Any) -> str | None:
    if valor is None:
        return None
    texto = str(valor).strip()
    return None if texto in ("", "null") else texto
