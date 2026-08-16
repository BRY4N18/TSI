"""Servicio del listado de despachos — L2.

`en_transito` se calcula aquí igual que se filtra en el repositorio: **desde las
horas del propio despacho**. Que las dos formas coincidan es lo que hace que
filtrar por «en tránsito» y leer el campo `en_transito` den la misma respuesta —
si divergieran, el listado se contradiría a sí mismo dentro de la misma página.
"""

from __future__ import annotations

from typing import Any

from core.informes.formato import a_iso
from core.informes.paginacion import Orden, Pagina
from core.repositories.seguimiento.informes_despachos_repository import (
    CURSOR_DESPACHOS,
    ORDEN_DESPACHOS,
    SIN_HORA,
    InformesDespachosRepository,
)


class InformesDespachosService:
    def __init__(self, repo: InformesDespachosRepository | None = None):
        self.repo = repo or InformesDespachosRepository()

    def despachos(
        self,
        *,
        cursor: tuple[Any, ...] | None = None,
        limit: int = 50,
        orden: Orden = ORDEN_DESPACHOS,
        idorigendespacho: int | None = None,
        idunidademergencia: int | None = None,
        idaccidente: str | None = None,
        en_transito: bool | None = None,
        desde_ms: int | None = None,
        hasta_ms: int | None = None,
    ) -> Pagina:
        crudas = self.repo.despachos(
            cursor=cursor,
            limit=limit,
            orden=orden,
            idorigendespacho=idorigendespacho,
            idunidademergencia=idunidademergencia,
            idaccidente=idaccidente,
            en_transito=en_transito,
            desde_ms=desde_ms,
            hasta_ms=hasta_ms,
        )
        pagina = CURSOR_DESPACHOS.recortar(crudas, limit)

        unidades = self.repo.unidades(
            [f.get("idunidademergencia") for f in pagina.filas]
        )
        origenes = self.repo.origenes(
            [f.get("idorigendespacho") for f in pagina.filas]
        )

        return pagina._replace(
            filas=[
                {
                    "numero_caso": fila.get("idaccidente"),
                    "unidad": unidades.get(fila.get("idunidademergencia")),
                    "origen_despacho": origenes.get(fila.get("idorigendespacho")),
                    "fecha_despacho": a_iso(fila.get("fechahoradespacho")),
                    # `0` es «aún no ha ocurrido», no 1970.
                    "fecha_llegada": _hora(fila.get("fechahorallegada")),
                    "fecha_retiro": _hora(fila.get("fechahoraretiro")),
                    # La traza de que la central retiró a la unidad, en vez de
                    # que la unidad terminara su parte.
                    "retiro_forzado": bool(fila.get("retiro_forzado")),
                    "en_transito": _en_transito(fila),
                }
                for fila in pagina.filas
            ]
        )


def _valor(valor: Any) -> int:
    try:
        return int(valor or SIN_HORA)
    except (TypeError, ValueError):
        return SIN_HORA


def _hora(valor: Any) -> str | None:
    return None if _valor(valor) <= SIN_HORA else a_iso(valor)


def _en_transito(fila: dict[str, Any]) -> bool:
    """Despachada, sin llegada y sin retiro: está en camino.

    Misma regla que el filtro del repositorio. No se consulta el histórico de
    estados del despacho (research D5).
    """
    return (
        _valor(fila.get("fechahoradespacho")) > SIN_HORA
        and _valor(fila.get("fechahorallegada")) <= SIN_HORA
        and _valor(fila.get("fechahoraretiro")) <= SIN_HORA
    )
