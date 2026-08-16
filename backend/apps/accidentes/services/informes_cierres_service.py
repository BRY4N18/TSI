"""Servicio del listado de cierres — L5.

⚠️ Una calificación ausente se devuelve ausente, **nunca como cero**.

En una escala de calificación, cero es el peor valor posible. Presentar «no se
calificó» como «se calificó con la nota mínima» invertiría el significado justo
donde más engaña: un promedio que incluyera esos ceros hundiría la media, y la
conclusión sería la contraria de lo que dicen los datos.
"""

from __future__ import annotations

from typing import Any

from core.informes.paginacion import Orden, Pagina
from core.repositories.accidentes.informes_cierres_repository import (
    CURSOR_CIERRES,
    ORDEN_CIERRES,
    SIN_TEXTO,
    InformesCierresRepository,
)


class InformesCierresService:
    def __init__(self, repo: InformesCierresRepository | None = None):
        self.repo = repo or InformesCierresRepository()

    def cierres(
        self,
        *,
        cursor: tuple[Any, ...] | None = None,
        limit: int = 50,
        orden: Orden = ORDEN_CIERRES,
        resultado: str | None = None,
        sin_observaciones: bool | None = None,
        con_calificacion: bool | None = None,
    ) -> Pagina:
        crudas = self.repo.cierres(
            cursor=cursor,
            limit=limit,
            orden=orden,
            resultado=resultado,
            sin_observaciones=sin_observaciones,
            con_calificacion=con_calificacion,
        )
        pagina = CURSOR_CIERRES.recortar(crudas, limit)

        return pagina._replace(
            filas=[
                {
                    "numero_caso": fila.get("idaccidente"),
                    "resultado_atencion": _vacio_a_none(
                        fila.get("resultado_atencion")
                    ),
                    # ⚠️ Ausente, nunca cero.
                    "calificacion": _calificacion(fila.get("calificacion")),
                    # Un cierre sin observaciones llega ausente, no como cadena
                    # vacía: «no escribió nada» y «escribió la cadena vacía» no
                    # son la misma afirmación sobre la calidad del cierre.
                    "observaciones_finales": _vacio_a_none(
                        fila.get("observaciones_finales")
                    ),
                }
                for fila in pagina.filas
            ]
        )


def _calificacion(valor: Any) -> int | None:
    """Solo una calificación positiva es una calificación.

    El centinela de un INT ausente en Pinot es un negativo grande, y `0` no está
    en la escala: los dos significan «no se calificó».
    """
    if valor is None:
        return None
    try:
        entero = int(valor)
    except (TypeError, ValueError):
        return None
    return entero if entero > 0 else None


def _vacio_a_none(valor: Any) -> str | None:
    if valor is None:
        return None
    texto = str(valor).strip()
    return None if texto in SIN_TEXTO else texto
